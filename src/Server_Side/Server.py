import os
import sys
import time
from socket import *
from threading import *
from Common import *

# TODO: Add command to display all connected clients

# note: message[0] is the protocol, and message[1] is the actual message

""" GLOBALS """

PING_PORT = 50000  # port that handles initial connection
SERVER_PORT = 55000  # start of server ports as per description
FILE_PORT = 55001
MTU = 1500
client_list = []
window_size = 1  # for selective repeat, this must match the same variable in Client.py
timeout = 5  # seconds

running = True

""" ******* """

clients_socket = socket(AF_INET, SOCK_STREAM)
clients_socket.bind(('', SERVER_PORT))
clients_socket.listen(15)  # we allow 15 connections max, so at worst we will need to queue 15 requests.


# ***** Preparing Files ***** #

def prepare_file(filename) -> list:
    packet_list = []
    location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    with open(os.path.join(location + "\\Files", filename), "rb") as file:
        while packet := file.read(MTU - 10):
            packet_list.append(packet)
    return packet_list


# ***** Preparing Files ***** #

print("Ready to serve on port ", SERVER_PORT)


def receive_message(sock: socket):
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

# TODO: send a complete TestImage.jpg - currently only one package go through
def file_sender(connection, client_addr, packet_list) -> None:
    connection.settimeout(timeout * 2)
    connection.sendto(str(len(packet_list)).encode(), client_addr)
    index = 0
    ack_list = []
    for i in range(0, len(packet_list)):
        ack_list.append(False)
    acked = 0
    cwnd = 1
    # threshold = 0
    first_loss = False
    halfway_flag = True

    print("sending files!, last byte is:", bytearray(packet_list[-1])[-1])

    while index != len(packet_list):
        window_frame = min(index + window_size,
                           len(packet_list))  # window_frame ensures were in the bounds of the list
        for i in range(index, window_frame):
            if not ack_list[i]:
                checksum = calc_checksum(packet_list[i])
                packet = transform_packet(i, checksum, packet_list[i], cwnd)  # "cooking" the packet.
                connection.sendto(packet, client_addr)

        buffer = []  # for lost packets!

        checker = index

        for i in range(index, window_frame):
            response, addr = receive_message(connection)
            threshold = cwnd / 2

            # ******************************************************************** #
            # TODO: maybe redundant - consider doing this only if receiving a NACK, then going over
            # TODO: packages that were'nt ACK'ed nor NACK'ed
            if response == "TIMEOUT":
                if not first_loss:
                    first_loss = True
                    print("first loss event is a:", response)
                cwnd = 1
                # buffer.append(packet_list[i])

            elif response[0] == "NACK":
                if not first_loss:
                    first_loss = True
                    print("first loss event is a:", response)
                cwnd -= 1
                buffer.append(int(response[1]))
            # ******************************************************************** #

            if response[0] == "ACK":
                acked += 1
                if not first_loss:
                    cwnd *= 2
                else:
                    if cwnd < threshold:
                        cwnd *= 2
                    else:
                        cwnd += 1
                if cwnd > 0.1 * len(packet_list):
                    cwnd = int(0.1 * len(packet_list))
                ack_list[int(response[1])] = True

            if acked == len(packet_list) / 2 or i >= 0.65 * len(packet_list) and halfway_flag:
                halfway_flag = False
                print("Halfway done!")
                # continue_req = struct.pack('LHI', 0x0000, 0x00, 0x0000) + "CONTINUE?".encode()
                continue_req = transform_packet(0, 0, "CONTINUE?".encode(), 0)
                connection.sendto(continue_req, client_addr)
                flag = False
                while not flag:  # should wait for response, but put in a loop as an extra measure.
                    res = connection.recv(4096).decode()
                    if res == "CONTINUE":
                        flag = True
                    elif res == "STOP":
                        print("User submitted STOP req - returning")
                        return

            if response[0] == "ACKALL":
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


def UDP_Threader(file_name) -> None:
    file_socket = socket(AF_INET, SOCK_DGRAM)
    file_socket.bind(('127.0.0.1', FILE_PORT))
    file_socket.settimeout(60)
    connection = file_socket

    msg, addr = receive_message(connection)
    if msg[0] == "HANDSHAKE":

        connection.sendto("ACK".encode(), addr)
        print("UDP Connection Established With " + str(addr[0]) + "," + str(addr[1]))

        response, addr = receive_message(connection)

        if response == "TIMEOUT":
            print("Client timed out!")
        elif "ACK" == response[0]:
            print("completed three-way handshake")
            file_sender(connection, addr, prepare_file(file_name))  # This handles selective repeat protocol!
        elif response[0] == "NACK":
            print("Client should specify what file")  # ... to complete the three way handshake!
    else:
        print("Could not establish connection")

    file_socket.close()


# ================================================================ #
#                             END UDP                              #
# ================================================================ #
# TODO: test functionality
def BroadcastToOne(message, connection):
    try:
        connection.send(message.encode())
    except IOError:
        connection.close()
        client_list.remove(connection)


def BroadcastToAll(message, connection):
    for client in client_list:
        if client[0] != connection:
            try:
                client[0].send(message.encode())

            except IOError:
                client[0].close()
                client_list.remove(client)


def find_by_name(name):
    for client in client_list:
        if client[1] == name:
            return client[0]
    return "NOT FOUND"


def get_client_list():
    return client_list


def Threader(connection: socket, address, name):
    while running:
        try:
            message = connection.recv(8192)
            message = message.decode()
            message = message.split('_', 1)

            if message:
                protocol = message[0]
                content = message[1]
                broadcast_msg = "<" + name + ">: " + str(content)

                if protocol == "ALL":
                    print(broadcast_msg)
                    BroadcastToAll(broadcast_msg, connection)
                elif protocol == "FILE":
                    udp_thread = Thread(target=UDP_Threader, args=[content])
                    udp_thread.start()
                    time.sleep(0.2)  # giving thread space to start.
                    connection.sendto(("FILE_" + content).encode(), address)
                else:  # if it's a private/direct message
                    connect = find_by_name(protocol)
                    BroadcastToOne(broadcast_msg, connect)

        except IOError:
            # Close client socket
            connection.close()


# suggestion : put a thread here that listens to exit events

try:
    while running:
        try:
            connection_socket, adr = clients_socket.accept()
            username = connection_socket.recv(4096).decode()
            client_list.append((connection_socket, username))
            print(username + " Connection from " + str(adr))
            client_thread = Thread(target=Threader, args=(connection_socket, adr, username))
            client_thread.start()
        except OSError:
            print("Something went wrong before threading the request!, the run will now stop.\n")
            # break
except IOError:  # TODO: consider as temorary?
    clients_socket.close()
    sys.exit()

# TODO: change the 'running' var in accordane with inputs like 'CTRL-C' or an exit event or an EOFError!
# TODO: suggestion - open a listener thread that will listen to this event/input
