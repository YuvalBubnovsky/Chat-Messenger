import sys
from socket import *
from threading import *

# TODO: Add command to display all connected clients
# TODO: Add "<user> has connected to chat!"

""" GLOBALS """

PING_PORT = 50000  # port that handles initial connection
SERVER_PORT = 55000  # start of server ports as per description
FILE_PORT = 55001
MTU = 1500
client_list = []

""" ******* """

allocator_socket = socket(AF_INET, SOCK_STREAM)
allocator_socket.bind(('', SERVER_PORT))
allocator_socket.listen(15)  # we allow 15 connections max, so at worst we will need to queue 15 requests.

print("Ready to serve on port \n", SERVER_PORT)

# ================================================================ #
#                               UDP                                #
# ================================================================ #

#TODO: Make this threaded
#TODO: Add check if user is on client_list while requesting file, deny if not

file_socket = socket(AF_INET, SOCK_DGRAM)
file_socket.bind(('', FILE_PORT))
file_socket.listen(15)

print("File port is ready on \n", FILE_PORT)

while True:
    msg, client_addr = file_socket.recvfrom(MTU)
    if msg.decode() == "HANDSHAKE":
        file_socket.sendto("ACK".encode(),client_addr)
        print("UDP Connection Established With %s:%s" % (client_addr[0], client_addr[1]))
    elif msg.decode() == "SEND":




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


# TODO : Verify this & Figure it out
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


def Threader(connection: socket, addr, name):
    while True:
        try:
            message = connection.recv(4096).decode()

            if message:
                message = message.split('_', 1)
                protocol = message[0]
                content = message[1]
                broadcast_msg = "<" + name + ">: " + str(content)

                if protocol == "ALL":
                    print(broadcast_msg)
                    BroadcastToAll(broadcast_msg, connection)
                elif protocol == "FILE":
                    pass
                else:  # if it's a private/direct message
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
