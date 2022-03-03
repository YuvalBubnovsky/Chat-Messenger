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
        self.response = ""

    def set_server_host(self, new_host):
        self.server_host = new_host

    def set_timeout(self, new_timeout: int):
        self.timeout = new_timeout

    def get_timeout(self):
        return self.timeout

    def set_cwnd(self, new_cwnd: int):
        self.cwnd = new_cwnd

    def get_cwnd(self):
        return self.cwnd

    def set_username(self, new_user: str):
        self.username = new_user

    def get_username(self):
        return self.username

    def set_response(self, new_response: str):
        self.response = new_response

    def get_response(self):
        return self.response

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
            return "TIMEOUT", -1, -1, -1, 10

        # ================================================================ #
        #                               UDP                                #
        # ================================================================ #

    def file_receiver(self, connection, server_addr, packet_list, fname) -> None:
        index = 0
        connection.settimeout(timeout)
        cwnd = 10

        while index != len(packet_list):
            print("cwnd:", cwnd)
            window_frame = min(index + cwnd + 2,
                               len(packet_list))  # window_frame ensures were in the bounds of the list
            for i in range(index, window_frame):
                packet, addr, seq_num, checksum, cwnd = self.receive_transformed_message(connection)

                if packet == "TIMEOUT" or cwnd == -1:
                    connection.sendto(("NACK_" + str(i)).encode(), server_addr)
                else:
                    try:
                        rsp = packet.decode()
                        rsp = rsp.split('_', 1)
                        if rsp[0] == "CONTINUE?":  # should happen around the 50% point of file transfer.
                            print("halfway done! continue?")
                            # ********TODO: when gui rolls around get input ************** #
                            # answer = input()
                            answer = "yes"
                            print("yes")  # CONTROL - TO BE REMOVED
                            # ^^^^^^^^TODO: when gui rolls around get input ^^^^^^^^^^^^^^ #
                            if answer == "yes":
                                connection.sendto("CONTINUE".encode(), server_addr)
                            else:
                                print("Relaying STOP file download to server")
                                connection.sendto("STOP".encode(), server_addr)
                                return
                        else:  # in this case the response is a modifed packet.
                            if calc_checksum(packet) == checksum:
                                packet_list[seq_num] = packet
                                connection.sendto(("ACK_" + str(seq_num)).encode(), server_addr)
                                index += 1
                            else:
                                print("Sending NACK!")
                                connection.sendto(("NACK_" + str(seq_num)).encode(), server_addr)
                    except UnicodeDecodeError:  # when not sending strings!
                        if calc_checksum(packet) == checksum:
                            packet_list[seq_num] = packet
                            connection.sendto(("ACK_" + str(seq_num)).encode(), server_addr)
                            index += 1
                        else:
                            print("Sending NACK!")
                            connection.sendto(("NACK_" + str(seq_num)).encode(), server_addr)

        connection.sendto("ACKALL".encode(), server_addr)
        print("Received all the packets and now assembling them to a file!")

        with open("downloaded_" + fname, "ab") as file:
            for _ in packet_list:
                if _ is not None:  # even after RDT some packets may be missing - this is a precaution.
                    file.write(_)

    def handshakes(self, sock, addr) -> bool:
        try:
            sock.sendto("HANDSHAKE_".encode(), addr)

            res, addr = self.receive_message(sock)
            if res[0] == "ACK":
                print("Server Is Live!")
            else:
                print("No Server response - try again")
                return False

            sock.sendto("ACK".encode(), addr)  # also completes the three-way handshake
        except OSError:
            print("timed out")

        return True

    def UDP_Threader(self, filename) -> None:
        server_addr = (self.server_host,self.udp_port)
        File_Socket = socket(AF_INET, SOCK_DGRAM)
        File_Socket.settimeout(60)
        File_Socket.connect(server_addr)

        print("attempting to confirm connection with a three way handshake.")

        if self.handshakes(File_Socket, server_addr):
            print("twh success")
            packets_len = File_Socket.recv(4096).decode()
            packet_list = [None] * int(packets_len)
            # ^ mirroring the list being sent from server - allows skipping re-ordering later
            print("Preparing to receive %s packages" % packets_len)

            self.file_receiver(File_Socket, server_addr, packet_list, filename)
        else:
            print("Could not complete three way handshake with the server! - try again")
        File_Socket.close()

        # ================================================================ #
        #                             END UDP                              #
        # ================================================================ #

    def response_thread(self, client_socket):
        time.sleep(0.2)
        try:
            while self.running:
                res = client_socket.recv(8192)
                res = res.decode()
                res = res.split('_', 1)

                if res == "TIMEOUT":
                    print("Connection Timed Out")
                    sys.exit(0)

                if res[0] == "FILE":
                    threading.Thread(target=self.UDP_Threader, args=(res[1],)).start()
                else:
                    self.set_response(res)
                    print(res)
        except OSError:
            print("No Longer Receiving Messages")
            return

    def message_thread(self, client_socket):
        time.sleep(0.2)
        try:
            while self.running:
                message = input()
                if message == "FILE":
                    name = "Heavy.jpg"
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

    def stop(self):
        pass

