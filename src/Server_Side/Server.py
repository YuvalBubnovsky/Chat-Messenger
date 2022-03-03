import os
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
MTU = 1500
client_list = {}
window_size = 1  # for selective repeat, this must match the same variable in Client.py
timeout = 10  # seconds
connected = 0  # control for adding to dict

running = True

""" ******* """

clients_socket = socket(AF_INET, SOCK_STREAM)
clients_socket.bind(('', SERVER_PORT))
clients_socket.listen(15)  # we allow 15 connections max, so at worst we will need to queue 15 requests.
print("Ready to serve on port ", SERVER_PORT)


def prepare_file(filename) -> list:
    packet_list = []
    location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    with open(os.path.join(location + "\\Files", filename), "rb") as file:
        while packet := file.read(MTU - 10):
            packet_list.append(packet)
    return packet_list


def username_exists(name):
    for key, value in client_list.items():
        if value[1] == name:
            return True
    return False


def display_connected():
    print("those connected are:")
    if len(client_list) == 0:
        print("No one :(")
    else:
        for key, value in client_list.items():
            print(value[1])


def dc_user(name):
    for key, value in client_list.items():
        if value[1] == name:
            del client_list[key]
            break


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


def file_sender(connection, client_addr, packet_list) -> None:
    connection.settimeout(timeout * 2)
    connection.sendto(str(len(packet_list)).encode(), client_addr)
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
            if not ack_list[i]:
                checksum = calc_checksum(packet_list[i])
                packet = transform_packet(i, checksum, packet_list[i], cwnd)  # "cooking" the packet.
                connection.sendto(packet, client_addr)

        checker = index

        for i in range(index, window_frame):
            response, addr = receive_message(connection)
            threshold = cwnd / 2

            if response == "TIMEOUT":
                if not first_loss:
                    first_loss = True
                    print("first loss event is a:", response)
                cwnd = 10
            elif response[0] == "NACK":
                if not first_loss:
                    first_loss = True
                    print("first loss event is a:", response)
                if cwnd > 15:
                    cwnd -= 1
            # explaining this segment - we know which packets to re-send based on whether they were ACK'ed or not
            # therefore, our only use for NACK's or Timeouts is CC.

            if response[0] == "ACK":
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
                ack_list[int(response[1])] = True

            if acked == len(packet_list) / 2 or i >= 0.65 * len(packet_list) and halfway_flag:
                halfway_flag = False
                print("Halfway done!")
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


def handshakes(connection):
    msg, addr = receive_message(connection)
    if msg[0] == "HANDSHAKE":

        connection.sendto("ACK".encode(), addr)
        print("Establishing UDP connection with " + str(addr[0]) + "," + str(addr[1]))

        response, addr = receive_message(connection)

        if response == "TIMEOUT":
            print("Client timed out!")
            return False, -1
        elif "ACK" == response[0]:
            print("completed three-way handshake")
            return True, addr
        elif response[0] == "NACK":
            print("Client should specify what file")  # ... to complete the three way handshake!
            return False, -1
    else:
        print("Could not establish connection")
        return False, -1


def UDP_Threader(file_name) -> None:
    file_socket = socket(AF_INET, SOCK_DGRAM)
    file_socket.bind(('127.0.0.1', FILE_PORT))
    file_socket.settimeout(60)
    connection = file_socket

    print("attempting to confirm connection with a three way handshake.")

    twh, addr = handshakes(connection)
    if twh:
        print("twh success!")
        file_sender(connection, addr, prepare_file(file_name))  # This handles selective repeat protocol!
    else:
        print("Could not complete the three way handshake :(")

    file_socket.close()


# ================================================================ #
#                             END UDP                              #
# ================================================================ #
def BroadcastToOne(message, connection):
    try:
        connection[0].send(message.encode())
    except IOError:
        connection[0].close()
        for key, value in client_list.items():
            if value[1] == connection[1]:
                del client_list[key]
                break


def BroadcastToAll(message, connection):
    for key, value in client_list.items():
        if value[0] != connection:
            try:
                value[0].send(message.encode())
            except IOError:
                value[0].close()
                del client_list[key]


def find_by_name(name):
    for key, value in client_list.items():
        if value[1] == name:
            return value
    return "NOT FOUND"


def Threader(connection: socket, address, name):
    while running:
        try:
            message = connection.recv(8192)
            message = message.decode()
            message = message.split('_', 1)

            if message:
                protocol = message[0]
                content = message[1]

                if protocol == "ALL":
                    broadcast_msg = "<" + name + ">: " + str(content)
                    print(broadcast_msg)
                    BroadcastToAll(broadcast_msg, connection)
                elif protocol == "FILE":
                    udp_thread = Thread(target=UDP_Threader, args=[content])
                    udp_thread.start()
                    time.sleep(0.2)  # giving thread space to start.
                    connection.sendto(("FILE_" + content).encode(), address)
                elif protocol == "DC":
                    dc_user(name)
                    print(name, "disconnected!")
                    display_connected()
                    return
                else:  # if it's a private/direct message
                    connect = find_by_name(protocol)
                    broadcast_msg = "<PM-" + name + ">: " + str(content)
                    BroadcastToOne(broadcast_msg, connect)

        except IOError:
            # Close client socket
            connection.close()


# suggestion : put a thread here that listens to exit events

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
                client_list[connected] = (connection_socket, username)
                connected += 1
                # client_list.append((connection_socket, username))
                print(username + " Connected!")
                client_thread = Thread(target=Threader, args=(connection_socket, adr, username))
                client_thread.start()
        except OSError:
            print("Something went wrong before threading the request!, the run will now stop.\n")
            # break
except IOError:
    clients_socket.close()
    sys.exit()

# TODO: change the 'running' var in accordane with inputs like 'CTRL-C' or an exit event or an EOFError!
# TODO: suggestion - open a listener thread that will listen to this event/input