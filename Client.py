"""
1. connects to Server on Port 50000 - allocator port
2. connects to a free port ( 55000 - 55015 ) which he was told by the allocator
3. uses the chat, etc...
"""

from socket import *
from threading import Thread
import sys
from Common import *

""" GLOBALS """

# serverHost = "192.168.1.215"
serverHost = "127.0.0.1"
serverPort = 55000
udp_port = 55001
username = sys.argv[1]
MTU = 1500
window_size = 1  # for selective repeat, this must match the same variable in Server.py
timeout = 5  # seconds
file_name = "temp"

running = True

""" ******* """


def receive_message(sock: socket):
    try:
        msg, address = sock.recvfrom(8192)
        msg = msg.decode()
        msg = msg.split('_', 1)
        return msg, address
    except OSError:
        return "TIMEOUT", -1


def receive_transformed_message(sock: socket):
    try:
        transformed_msg, address = sock.recvfrom(8192)
        temp, packet = unpack_transformed_packet(transformed_msg)
        seq_num = temp[0]
        checksum = temp[1]
        return packet, address, seq_num, checksum
    except OSError:
        return "TIMEOUT", -1, -1, -1

# ================================================================ #
#                               UDP                                #
# ================================================================ #


def UDP_Threader(filename) -> None:
    server_addr = (serverHost, udp_port)
    File_Socket = socket(AF_INET, SOCK_DGRAM)
    File_Socket.settimeout(60)
    File_Socket.connect(server_addr)

    File_Socket.sendto("HANDSHAKE_".encode(), server_addr)

    response, addr = receive_message(File_Socket)
    if response[0] == "ACK":
        print("Server Is Live!")
    else:
        print("No Server response - try again")  # TODO: try 3-4 times before breaking. - consider not doing
        return

    File_Socket.sendto("ACK".encode(), server_addr)  # also completes the three-way handshake

    packets_len = File_Socket.recv(4096).decode()
    packet_list = [None] * int(packets_len)  # mirroring the list being sent from server - allows skipping re-ordering later
    print("Preparing to receive %s packages" % packets_len)

    index = 0
    File_Socket.settimeout(timeout)

    while index != len(packet_list):
        window_frame = min(index + window_size,
                           len(packet_list))  # window_frame ensures were in the bounds of the list
        for i in range(index, window_frame):
            packet, addr, seq_num, checksum = receive_transformed_message(File_Socket)

            if response == "TIMEOUT":
                File_Socket.sendto(("NACK_" + str(i)).encode(), server_addr)
            else:
                try:
                    response = packet.decode()
                    response = response.split('_', 1)
                    if response[0] == "CONTINUE?":  # should happen around the 50% point of file transfer.
                        print("halfway done! continue?")
                        # answer = input()  #TODO: when gui rolls around get input
                        answer = "yes"
                        if answer == "yes":
                            print("yes")  # CONTROL - TO BE REMOVED
                            File_Socket.sendto("CONTINUE".encode(), server_addr)
                        else:
                            print("Relaying STOP file download to server")
                            File_Socket.sendto("STOP".encode(), server_addr)
                            index = len(packet_list)  # effectively breaking.
                            continue
                    else:  # in this case the response is a modifed packet.
                        if calc_checksum(packet) == checksum:
                            packet_list[seq_num] = packet
                            File_Socket.sendto(("ACK_" + str(seq_num)).encode(), server_addr)
                            index += 1
                        else:
                            print("Sending NACK!")
                            File_Socket.sendto(("NACK_" + str(seq_num)).encode(), server_addr)
                except UnicodeDecodeError:  # when not sending strings!
                    if calc_checksum(packet) == checksum:
                        packet_list[seq_num] = packet
                        File_Socket.sendto(("ACK_" + str(seq_num)).encode(), server_addr)
                        index += 1
                    else:
                        print("Sending NACK!")
                        File_Socket.sendto(("NACK_" + str(seq_num)).encode(), server_addr)


    File_Socket.sendto("ACKALL".encode(), server_addr)
    print("Received all the packets and now assembling them to a file!")

    with open("downloaded_" + filename, "ab") as file:
        for _ in packet_list:
            file.write(_)

    File_Socket.close()


# ================================================================ #
#                             END UDP                              #
# ================================================================ #

def response_thread(client_socket):
    try:
        while running:
            response = client_socket.recv(8192)
            response = response.decode()
            response = response.split('_', 1)

            if response == "TIMEOUT":
                print("connection timed out")  # we do not expect a timeout here!
                sys.exit(0)

            if response[0] == "FILE":
                t = Thread(target=UDP_Threader, args=[response[1]])
                t.start()
            else:
                print(response)
    except OSError:
        print("No longer receiving messages")
        return


def message_thread(client_socket):
    try:
        while running:
            message = input()
            if message == "FILE":
                name = "TestFile.txt"
                clientSocket.send(("FILE_" + name).encode())
            else:
                client_socket.send(message.encode())
    except OSError:
        print("No longer sending messages")
        return
    finally:
        client_socket.close()


try:
    # TODO: remove automatic connection and add a protocol to connect.
    clientSocket = socket(AF_INET, SOCK_STREAM)
    print("Socket Created")
    clientSocket.connect((serverHost, serverPort))
    print("Connected to: " + serverHost + " on port: " + str(serverPort))
    clientSocket.send(username.encode())
    t1 = Thread(target=response_thread, args=[clientSocket])
    t2 = Thread(target=message_thread, args=[clientSocket])
    t1.start()
    t2.start()

except IOError:
    print("An error has occurred, please try again\r\n Closing client connection")
    sys.exit(1)
