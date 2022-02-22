import sys
from socket import *
from threading import *
import time
import struct
from Common import *

# TODO: Add command to display all connected clients
# TODO: Add "<user> has connected to chat!"

# note: message[0] is the protocol, and message[1] is the actual message

""" GLOBALS """

PING_PORT = 50000  # port that handles initial connection
SERVER_PORT = 55000  # start of server ports as per description
FILE_PORT = 55001
MTU = 1500
client_list = []
window_size = 10  # for selective repeat, this must match the same variable in Client.py
timeout = 5  # seconds
file_name = "temp"

""" ******* """

clients_socket = socket(AF_INET, SOCK_STREAM)
file_socket = socket(AF_INET, SOCK_DGRAM)
clients_socket.bind(('', SERVER_PORT))
file_socket.bind(('', FILE_PORT))
clients_socket.listen(15)
file_socket.listen(15)  # we allow 15 connections max, so at worst we will need to queue 15 requests.

print("Ready to serve on port \n", SERVER_PORT)


def receive_message(sock: socket):
    try:
        msg, client_addr = sock.recvfrom(MTU)
    except:
        return "TIMEOUT"

    msg = msg.decode()
    msg = msg.split('_', 1)
    return msg, client_addr


# ================================================================ #
#                               UDP                                #
# ================================================================ #

# TODO: Add check if user is on client_list while requesting file, deny if not
def file_sender(connection, client_addr, packet_list, filename) -> None:
    index = 0

    while index != len(packet_list):
        buffer = [window_size]  # re(set) buffer
        window_frame = min(index + window_size,
                           len(packet_list) - 1)  # window_frame ensures were in the bounds of the list
        for i in range(index, window_frame):
            buffer.append(packet_list[i])
        for packet in buffer:
            connection.sendto(packet, client_addr)

        # time.sleep(timeout*2)  # waiting for responses to arrive
        index_buffer = []

        for i in range(index, window_frame):
            response = receive_message(connection)

            if response == "TIMEOUT":
                connection.send(packet_list[i])
            elif response[0] == "NACK":
                connection.send(packet_list[i])

            if response[0] == "ACK":

                if int(response[1]) - 1 == index:
                    index += 1

            if response == "ACKALL":
                index = len(packet_list) # essentially breaking.


def UDP_Threader(connection: socket) -> None:
    msg, client_addr = receive_message(connection)
    if msg[0] == "HANDSHAKE":

        connection.send("ACK".encode(), client_addr)
        print("UDP Connection Established With %s:%s" % (client_addr[0], client_addr[1]))

        response = receive_message(connection)
        if filename := response[0]:
            filename = file_name
            packet_list = []  # this will represent the file packets in a sequential manner for selective-repeat
            try:
                with open(filename, "rb") as file:
                    seq_num = 0
                    while packet := file.read(MTU - 100):
                        checksum = calc_checksum(packet)
                        packet = transform_packet(seq_num, checksum, packet)  # "cooking" the packet.
                        packet_list.append(packet)
                        seq_num += 1
            finally:
                file_sender(connection, client_addr, packet_list, filename)

        elif response[0] == "NACK":
            print("Client should specify what file")  # ... to complete the three way handshake!
    else:
        print("Could not establish connection")


# ================================================================ #
#                             END UDP                              #
# ================================================================ #

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
    return "all"  # TODO: remove this


def Threader(connection: socket, name):
    while True:
        try:
            message, _ = receive_message(connection)

            if message:
                protocol = message[0]
                content = message[1]
                broadcast_msg = "<" + name + ">: " + str(content)

                if protocol == "ALL":
                    print(broadcast_msg)
                    BroadcastToAll(broadcast_msg, connection)
                elif protocol == "FILE":
                    # TODO
                    pass
                else:  # if it's a private/direct message
                    connect = find_by_name(protocol)
                    BroadcastToOne(broadcast_msg, connect)

        except IOError:
            # Close client socket
            connection.close()


while True:
    try:
        connection_socket, address = clients_socket.accept()
        username = connection_socket.recv(4096).decode()
        client_list.append((connection_socket, username))
        # print("Connection from " + str(address))
        client_thread = Thread(target=Threader, args=(connection_socket, address, username))
        client_thread.start()

        # TODO: open this connection on TCP request from user!
        file_socket.settimeout(timeout * 2)
        file_conn_socket, addr = file_socket.accept()
        udp_thread = Thread(target=UDP_Threader, args=(file_conn_socket, addr))
        udp_thread.start()


    except OSError:
        print("Something went wrong before threading the request!, the run will now stop.\n")
        break

clients_socket.close()
file_socket.close()
sys.exit()
