import sys
from socket import *
from threading import *

""" GLOBALS """

PING_PORT = 50000  # port that handles initial connection
SERVER_PORT = 55000  # start of server ports as per description
client_list = []

""" ******* """

allocator_socket = socket(AF_INET, SOCK_STREAM)
allocator_socket.bind(('', SERVER_PORT))
allocator_socket.listen(15)  # we allow 15 connections max, so at worst we will need to queue 15 requests.

print("Ready to serve on port ", SERVER_PORT)


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
    return "all" #TODO: remove this


def Threader(connection: socket, addr, name):
    while True:
        try:
            message = connection.recv(4096).decode()

            if message:
                protocol = message[1]
                content = message[0]
                broadcast_msg = "<" + name + ">: " + str(content)
                if protocol is all:
                    print(broadcast_msg)
                    BroadcastToAll(broadcast_msg, connection)
                else:
                    connect = find_by_name(protocol)
                    BroadcastToOne(broadcast_msg, connect)

        except IOError:
            # Close client socket
            connection.close()


while True:
    try:
        connection_socket, address = allocator_socket.accept()
        username = connection_socket.recv(4096).decode()
        client_list.append((connection_socket, username))
        # print("Connection from " + str(address))
        thread = Thread(target=Threader, args=(connection_socket, address, username))
        thread.start()

    except OSError:
        print("Something went wrong before threading the request!, the run will now stop.\n")
        break

allocator_socket.close()
sys.exit()
