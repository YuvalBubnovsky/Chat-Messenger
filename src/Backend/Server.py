import os
import pickle  # Allows
import socket
import sys
import time
from socket import *
from threading import *
from Common import *

# note: message[0] is the protocol, and message[1] is the actual message

""" GLOBALS """

PING_PORT = 50000  # port that handles initial connection
SERVER_PORT = 55000  # start of server ports as per description
FILE_PORT = 55001
TCP_PORT = 60000
MTU = 1500
client_list = []
window_size = 1  # for selective repeat, this must match the same variable in Client.py
timeout = 10  # seconds
control = 0  # used for cycling through ports

running = True

""" ******* """

clients_socket = socket(AF_INET, SOCK_STREAM)
clients_socket.bind(('', SERVER_PORT))
clients_socket.listen(15)  # we allow 15 connections max, so at worst we will need to queue 15 requests.
print("Ready to serve on port ", SERVER_PORT)


def prepare_file(filename) -> list:
    """
    breaks the file into packets of size 1490 and sorts them into a list
    :param filename: the name of the file
    :return: a sorted list contating the packets of the file
    """
    packet_list = []
    print(__file__)
    location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    location = os.path.join(location, "Files")
    with open(os.path.join(location, filename), "rb") as file:
        while packet := file.read(MTU - 10):
            packet_list.append(packet)
    return packet_list


def user_list() -> list:
    """
    this method constructs a list of our users names and returns it
    :return: a list of strings
    """
    lst = []
    for client in client_list:
        lst.append(client[1])
    lst.append("USERS")  # for protocol usage!
    return lst


def file_list() -> list:
    """
        this method constructs a list of our available files and returns it
        :return: a list of strings
        """
    location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    location = os.path.join(location, "Files")
    location = os.fsencode(location)
    names_lst = []
    for file in os.listdir(location):
        filename = os.fsdecode(file)
        names_lst.append(filename)

    names_lst.append("FILES") # for protocol usage!
    return names_lst


def username_exists(name):
    """
    checks if a name is a taken username
    :param name: string
    :return: bool
    """
    for client in client_list:
        if client[1] == name:
            return True
    return False


def display_connected():
    """
    self-explanatory, this is server side only.
    :return: none
    """
    print("those connected are:")
    if len(client_list) == 0:
        print("No one :(")
    else:
        for client in client_list:
            print(client[1])


def dc_user(name):
    """
    this method removes a user based on his unique username
    :param name: string
    :return: none
    """
    for client in client_list:
        if client[1] == name:
            client_list.remove(client)
            break


def receive_message(sock: socket):
    """
    this method receives a message using the socket and then also breaks it into segments
    of protocol and the actual message and returns them as a pair
    :param sock: socket
    :return: list, tuple
    """
    try:
        msg, address = sock.recvfrom(8192)
        msg = msg.decode()
        msg = msg.split('_', 1)
        return msg, address
    except TimeoutError:
        return "TIMEOUT", -1


# ================================================================ #
#                               UDP                                #
# ================================================================ #


def file_sender(connection, client_addr, packet_list) -> None:
    """
    This method implements RDT with selective repeat, rolling window, and CC.
    :param connection: socket
    :param client_addr: tuple
    :param packet_list: list of byte objects
    :return: none
    """
    connection.settimeout(timeout * 2)
    index = 0
    ack_list = []
    for i in range(0, len(packet_list)):
        ack_list.append(False)
    acked = 0
    cwnd = 10
    first_loss = False
    halfway_flag = True

    print("sending files!, last byte is:", bytearray(packet_list[-1])[-1])

    while index != len(packet_list):
        print("cwnd:", cwnd)

        window_frame = min(index + cwnd,
                           len(packet_list))  # window_frame ensures were in the bounds of the list
        for i in range(index, window_frame):
            if halfway_flag:
                if acked == len(packet_list) / 2:
                    i = i + 1
                    halfway_flag = False
                    print("Halfway done!")
                    continue_req = transform_packet(0, 0, "CONTINUE?".encode(), 0)
                    connection.sendto(continue_req, client_addr)
                    try:
                        res = connection.recv(4096).decode()
                        if res == "CONTINUE":
                            print("Continuing!")
                        elif res == "STOP":
                            print("User submitted STOP req - returning")
                            return
                    except IOError:
                        print("client timed out during continue request - stopping!")
                        return
            if not ack_list[i]:
                checksum = calc_checksum(packet_list[i])
                packet = transform_packet(i, checksum, packet_list[i], cwnd)  # "cooking" the packet.
                connection.sendto(packet, client_addr)

        checker = index

        for i in range(index, window_frame):
            res, addr = receive_message(connection)
            threshold = cwnd / 2

            if res == "TIMEOUT" or res[0] == "TIMEOUT":
                if not first_loss:
                    first_loss = True
                    print("first loss event is a:", res)
                cwnd = 10
            elif res[0] == "NACK":
                if not first_loss:
                    first_loss = True
                    print("first loss event is a:", res)
                if cwnd > 10:
                    cwnd -= 1
            # explaining this segment - we know which packets to re-send based on whether they were ACK'ed or not
            # therefore, our only use for NACK's or Timeouts is CC.

            if res[0] == "ACK":
                acked += 1
                if not first_loss:
                    cwnd *= 2
                else:
                    if cwnd < threshold:
                        cwnd *= 2
                    else:
                        cwnd += 1
                if cwnd > 0.1 * len(packet_list):  # making sure window isn't bloating!
                    cwnd = int(0.1 * len(packet_list))
                ack_list[int(res[1])] = True

            if res[0] == "ACKALL":
                print("All packets were received!")
                index = len(packet_list)  # essentially breaking.
                continue

            if index != len(packet_list):  # the idea is to ack the current index position
                if ack_list[index]:
                    index += 1

        if index != len(packet_list):
            for i in range(index, checker + window_frame + 1):  # checking if any index increments were missed.
                if ack_list[i]:
                    index += 1
                else:
                    break
    print("done!")


def handshakes(connection) -> (bool, any):
    """
    this method attempts to handshake with the client by bruteforce
    :param connection: socket
    :return: (True,socket) on success or (False, -1) on error
    """
    step1 = False
    msg = ""
    addr = ""
    for _ in range(0, 5):
        try:
            temp1, temp2 = receive_message(connection)
            if temp1 == "TIMEOUT":
                continue
            if not step1:
                msg = temp1
                addr = temp2
                step1 = True
        except IOError:
            continue
    if msg == "" or addr == "":
        print("packet lose 2 stronk")
        return False

    if msg[0] == "HANDSHAKE":

        for _ in range(0, 5):
            connection.sendto("ACK".encode(), addr)

        time.sleep(1)

        print("Establishing UDP connection with " + str(addr[0]) + "," + str(addr[1]))

        response = ""
        addr = ""
        step3 = False  # step2 is on client side ( a similar code block )
        for _ in range(0, 5):
            try:
                temp1, temp2 = receive_message(connection)
                if temp1 == "TIMEOUT":
                    continue
                if not step3:
                    response = temp1
                    addr = temp2
                    step3 = True
            except IOError:
                continue

        if response == "" or addr == "":
            print("Client timed out!")
            return False, -1

        if "ACK" == response[0]:
            print("completed three-way handshake")
            return True, addr
        elif response[0] == "NACK":
            print("Client should specify what file")  # ... to complete the three way handshake!
            return False, -1
    else:
        print("Could not establish connection")
        return False, -1


def UDP_Threader(file_name, port) -> None:
    """
    this thread only opens when relevant protocol is received and is in charge of Reliable UDP file transfer
    :param file_name: name of the file to be transferred
    :param port: avaialbe port
    :return: none
    """
    file_socket = socket(AF_INET, SOCK_DGRAM)
    file_socket.bind(('127.0.0.1', port))
    file_socket.settimeout(60)
    connection = file_socket

    print("attempting to confirm connection with a three way handshake.")

    twh, addr = handshakes(connection)
    if twh:
        print("twh success!")
        packets = prepare_file(file_name)
        for _ in range(0, 5):
            # length = transform_packet(0,0,str(len(packets)).encode(),0)
            connection.sendto(("length_" + str(len(packets))).encode(), addr)
            # connection.sendto(length, addr)
        time.sleep(1)
        print("sent")
        file_sender(connection, addr, packets)  # This handles selective repeat protocol!
    else:
        print("Could not complete the three way handshake :(")

    file_socket.close()


# ================================================================ #
#                             END UDP                              #
# ================================================================ #

def BroadcastToOne(message, connection):
    """
    receives a message and attemtps to send it to one user
    this requires that the protocol part of the message will be
    the username of the user to be sent a private message
    that is - username_pm
    :param message: string
    :param connection: socket
    :return: none
    """
    try:
        connection[0].send(message.encode())
    except IOError:
        connection[0].close()
        for client in client_list:
            if client[1] == connection[1]:
                client_list.remove(client)
                break


def BroadcastToAll(message):
    """
    this method receives a message and broadcasts it to all connected users
    :param message: string
    :return: none
    """
    for client in client_list:
        try:
            client[0].send(message.encode())
        except IOError:
            client[0].close()
            client_list.remove(client)


def BroadcastList(lst):
    """
    broadcasts lst to everyone
    :param lst: list of strings
    :return: none
    """
    for client in client_list:
        try:
            client[0].send(pickle.dumps(lst))
        except IOError:
            client[0].close()
            client_list.remove(client)


def find_by_name(name):
    """
    iterates over the client list and attempts to find the client with username matching name
    :param name: string
    :return: tuple or "NOT FOUND" if none matched name
    """
    for client in client_list:
        if client[1] == name:
            return client
    return "NOT FOUND"


def tcp_file_sender(addr, filename):
    """
    this method sends a file over tcp
    :param addr: tuple
    :param filename: string
    :return: none
    """
    con = socket(AF_INET, SOCK_STREAM)
    con.connect(addr)

    location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    location = os.path.join(location, "Files")

    print("sending!")
    with open(os.path.join(location, filename), "rb") as file:
        packet = file.read(MTU)
        while packet:
            con.send(packet)
            packet = file.read(MTU)

    print("done!")
    con.close()


def Threader(connection: socket, address, name):
    """
    The main loop for any tcp connection coming to our server, and in charge of sorting the message to it's
    appropriate method based on its protocol
    :param connection: socket
    :param address: tuple
    :param name: string
    :return: none
    """
    while running:
        try:
            time.sleep(0.5)
            message = connection.recv(8192)
            message = message.decode()
            message = message.split('_', 1)

            if message:
                protocol = message[0]
                content = message[1]
                global control

                if protocol == "ALL":
                    broadcast_msg = "<" + name + ">: " + str(content)
                    print(broadcast_msg)
                    BroadcastToAll(broadcast_msg)
                    continue

                if protocol == "FILE":
                    port = FILE_PORT + control
                    control += 1

                    udp_thread = Thread(target=UDP_Threader, args=[content, port])
                    udp_thread.start()
                    time.sleep(2)  # giving thread space to start.
                    connection.sendto(("FILE_" + str(port) + "_" + content).encode(), address)
                    continue
                elif protocol == "TCPFILE":
                    port = TCP_PORT + control
                    control += 1
                    connection.sendto(("TCPFILE_" + str(port) + "_" + content).encode(), address)
                    time.sleep(2)
                    print(connection)  # giving thread space to start.
                    Thread(target=tcp_file_sender, args=[('127.0.0.1', int(port)), content]).start()
                    continue

                if protocol == "GETUSERS":
                    lst = user_list()
                    connection.sendto(pickle.dumps(lst), address)
                    continue

                if protocol == "WF":
                    lst = file_list()
                    connection.sendto(pickle.dumps(lst), address)
                    continue

                if protocol == "DC":
                    dc_user(name)
                    print(name, "disconnected!")
                    lst = user_list()
                    BroadcastList(lst)
                    display_connected()
                    return

                # else - if it's a private/direct message
                connect = find_by_name(protocol)
                broadcast_msg = "<PM-" + name + ">: " + str(content)
                BroadcastToOne(broadcast_msg, connect)

        except IOError:
            # Close client socket
            connection.close()


# main loop:
try:
    while running:
        try:
            connection_socket, adr = clients_socket.accept()
            username = connection_socket.recv(4096).decode()
            if username_exists(username):
                connection_socket.send("TAKEN_username".encode())
                continue
            else:
                connection_socket.send("CON_Connected".encode())
                client_list.append((connection_socket, username))
                # client_list.append((connection_socket, username))
                print(username + " Connected!")
                lst = user_list()
                time.sleep(2)
                BroadcastList(lst)
                client_thread = Thread(target=Threader, args=(connection_socket, adr, username))
                client_thread.start()
        except OSError:
            print("Something went wrong before threading the request!, the run will now stop.\n")
            # break
except IOError:
    clients_socket.close()
    sys.exit()
