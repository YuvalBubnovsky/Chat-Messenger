import threading
import time
from socket import *
from threading import Thread
import sys
from Common import *


class Client:

    def __init__(self, server_host, server_port, udp_port, username, MTU, timeout, running):
        self.server_host = server_host
        self.server_port = server_port
        self.udp_port = udp_port
        self.username = username
        self.MTU = MTU
        self.timeout = timeout
        self.running = running
        self.cwnd = 1

    def set_timeout(self, new_timeout: int):
        self.timeout = new_timeout

    def get_timeout(self):
        return self.timeout

    def set_cwnd(self, new_cwnd: int):
        self.cwnd = new_cwnd

    def get_cwnd(self):
        return self.cwnd

    def receive_message(self, sock: socket):
        try:
            msg, address = sock.recvfrom(8192)
            msg = msg.decode()
            msg = msg.split('_', 1)
            return msg, address
        except OSError:
            return "TIMEOUT", -1

    def receive_transformed_message(self, sock: socket):
        try:
            transformed_msg, address = sock.recvfrom(8192)
            temp, packet = unpack_transformed_packet(transformed_msg)
            seq_num = temp[0]
            checksum = temp[1]
            cwnd = temp[2]
            return packet, address, seq_num, checksum, cwnd
        except OSError:
            return "TIMEOUT", -1, -1, -1, -1

        # ================================================================ #
        #                               UDP                                #
        # ================================================================ #

    def UDP_Threader(self, filename) -> None:
        server_addr = (self.server_host, self.udp_port)
        File_Socket = socket(AF_INET, SOCK_DGRAM)
        File_Socket.settimeout(60)
        File_Socket.connect(server_addr)

        File_Socket.sendto("HANDSHAKE_".encode(), server_addr)
        response, addr = self.receive_message(File_Socket)

        if response[0] == "ACK":
            print("Server Is Live!")
        else:
            print("No Server Response - Try Again!")
            return

        File_Socket.sendto("ACK".encode(), server_addr)

        packets_len = File_Socket.recv(4096).decode()
        packet_list = [None] * int(packets_len)
        print("Preparing to receive %s packages" % packets_len)

        index = 0
        File_Socket.settimeout(self.get_timeout())
        self.set_cwnd(1)

        while index != len(packet_list):
            print("cwnd:", self.get_cwnd())
            window_frame = min(index + self.get_cwnd(), len(packet_list))
            for i in range(index, window_frame):
                packet, addr, seq_num, checksum, cwnd = self.receive_transformed_message(File_Socket)
                self.set_cwnd(cwnd)

                if response == "TIMEOUT":
                    File_Socket.sendto(("NACK_" + str(i)).encode(), server_addr)
                else:
                    try:
                        response = packet.decode()
                        response = response.split('_', 1)
                        if response[0] == "CONTINUE?":
                            print("Halfway Done! Continue?")
                            answer = "yes"
                            if answer == "yes":
                                print("yes")
                                File_Socket.sendto("CONTINUE".encode(), server_addr)
                            else:
                                print("Relaying STOP File Download To Server")
                                File_Socket.sendto("STOP".encode(), server_addr)
                                index = len(packet_list)
                                continue
                        else:
                            if calc_checksum(packet) == checksum:
                                packet_list[seq_num] = packet
                                File_Socket.sendto(("ACK_" + str(seq_num)).encode(), server_addr)
                                index += 1
                            else:
                                print("Sending NACK!")
                                File_Socket.sendto(("NACK_" + str(seq_num)).encode(), server_addr)
                    except UnicodeDecodeError:
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

    def response_thread(self, client_socket):
        time.sleep(0.2)
        try:
            while self.running:
                response = client_socket.recv(8192)
                response = response.decode()
                response = response.split('_', 1)

                if response == "TIMEOUT":
                    print("Connection Timed Out")
                    sys.exit(0)

                if response[0] == "FILE":
                    threading.Thread(target=self.UDP_Threader, args=(response[1],)).start()
                else:
                    print(response)
        except OSError:
            print("No Longer Receiving Messages")
            return

    def message_thread(self, client_socket):
        time.sleep(0.2)
        try:
            while self.running:
                message = input()
                if message == "FILE":
                    name = "TestFile.txt"
                    client_socket.send(("FILE_" + name).encode())
                else:
                    client_socket.send(message.encode())
        except OSError:
            print("No Longer Sending Messages")
            return
        finally:
            client_socket.close()

    def run(self):
        try:
            clientSocket = socket(AF_INET, SOCK_STREAM)
            print("Socket Created")
            clientSocket.connect((self.server_host, self.server_port))
            print("Connected to: " + self.server_host + " on port: " + str(self.server_port))
            clientSocket.send(self.username.encode())
            threading.Thread(target=self.message_thread, args=(clientSocket,)).start()
            threading.Thread(target=self.response_thread, args=(clientSocket,)).start()
        except IOError:
            print("An error has occurred, please try again\r\n Closing client connection")
            sys.exit(1)


if __name__ == '__main__':
    client = Client('127.0.0.1', 55000, 55001, "yuval", 1500, 5, True)
    Client.run(client)
