"""
1. connects to Server on Port 50000 - allocator port
2. connects to a free port ( 55000 - 55015 ) which he was told by the allocator
3. uses the chat, etc...
"""

from socket import *
from threading import Thread
import sys
import os
import time

serverHost = "192.168.1.215"
serverPort = 55000
udp_port = 55001
username = sys.argv[1]
MTU = 1500


# ================================================================ #
#                               UDP                                #
# ================================================================ #

# TODO: Make this threaded
def request_file():
    File_Socket = socket(AF_INET, SOCK_DGRAM)
    File_Socket.settimeout(10)

    File_Socket.sendto("HANDSHAKE".encode(), (serverHost, udp_port))
    server_response = get_response(File_Socket)
    if server_response == "ACK":
        print("Server Is Live! You Can Receive Files!\n")
    while True:
        File_Socket.sendto("SEND".encode(),(serverHost, udp_port))
        server_response = get_response(File_Socket)
        if server_response == "ACK":


def get_response(sock):
    try:
        rec_msg = sock.recvfrom(MTU)
        return rec_msg[0]
    except IOError:
        return "An Error Occured, Please Try Again!\n"


# ================================================================ #
#                             END UDP                              #
# ================================================================ #

def response_thread(client_socket):
    response = (client_socket.recv(4096)).decode()
    print(response)


def message_thread(client_socket):
    message = input()
    client_socket.send(message.encode())


# TODO: This also needs attention after were done with server side
def calculate_checksum(data):
    nleft = len(data)
    sum = 0
    pos = 0
    while nleft > 1:
        sum = ord(data[pos]) * 256 + (ord(data[pos + 1]) + sum)
        pos = pos + 2
        nleft = nleft - 2
    if nleft == 1:
        sum = sum + ord(data[pos]) * 256

    sum = (sum >> 16) + (sum & 0xFFFF)
    sum += (sum >> 16)
    sum = (~sum & 0xFFFF)

    return sum


def verify_checksum(data):
    nleft = len(data)
    sum = 0
    pos = 0
    while nleft > 1:
        sum = ord(data[pos]) * 256 + (ord(data[pos + 1]) + sum)
        pos = pos + 2
        nleft = nleft - 2
    if nleft == 1:
        sum = sum + ord(data[pos]) * 256

    cksum = calculate_checksum(data)
    flag = (cksum) ^ (sum)
    for bit in flag:
        if flag[bit] == 0:
            return False
        else:
            return True


# TODO: Switch the loop structure so we don't create INF threads
try:
    clientSocket = socket(AF_INET, SOCK_STREAM)
    print("Socket Created")
    clientSocket.connect((serverHost, serverPort))
    print("Connected to: " + serverHost + " on port: " + str(serverPort))
    clientSocket.send(username.encode())
    while True:
        t1 = Thread(target=response_thread, args=[clientSocket])
        t2 = Thread(target=message_thread, args=[clientSocket])
        t1.start()
        t2.start()


except IOError:
    print("An error has occurred, please try again\r\n Closing client connection")
    sys.exit(1)

clientSocket.close()
