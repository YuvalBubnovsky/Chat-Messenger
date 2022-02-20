"""
1. connects to Server on Port 50000 - allocator port
2. connects to a free port ( 55000 - 55015 ) which he was told by the allocator
3. uses the chat, etc...
"""

from socket import *
from threading import Thread
import sys


serverHost = "10.0.0.2"
serverPort = 55000
username = sys.argv[1]


def response_thread(client_socket):
    response = (client_socket.recv(4096)).decode()
    print(response)


def message_thread(client_socket):
    message = input()
    client_socket.send(message.encode())


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
