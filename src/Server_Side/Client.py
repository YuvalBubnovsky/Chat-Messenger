import os
import threading
import time
from socket import *
import sys
import pickle
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
        self.TCP_Socket = None
        self.file_list = []
        self.user_list = []
        self.res_flag = False
        self.user_flag = False
        self.taken_flag = False

    def set_res_flag(self, new_flag: bool):
        self.res_flag = new_flag

    def get_res_flag(self):
        return self.res_flag

    def set_user_flag(self, new_flag: bool):
        self.user_flag = new_flag

    def get_user_flag(self):
        return self.user_flag

    def set_TCP_Socket(self, sock):
        self.TCP_Socket = sock

    def get_TCP_Socket(self):
        return self.TCP_Socket

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

    def set_taken_flag(self, new_flag: bool):
        self.taken_flag = new_flag

    def get_taken_flag(self):
        return self.taken_flag

    def set_file_list(self, new_list: list):
        self.file_list = new_list

    def get_file_list(self):
        return self.file_list

    def set_user_list(self, new_list: list):
        self.user_list = new_list

    def get_user_list(self):
        return self.user_list

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
        connection.settimeout(self.timeout)
        cwnd = 10

        while index != len(packet_list):
            window_frame = min(index + cwnd + 2,
                               len(packet_list))  # window_frame ensures were in the bounds of the list
            for i in range(index, window_frame):
                packet, addr, seq_num, checksum, cwnd = self.receive_transformed_message(connection)

                if packet == "TIMEOUT" or seq_num == -1:
                    connection.sendto(("NACK_" + str(i)).encode(), server_addr)
                else:
                    try:
                        rsp = packet.decode()
                        rsp = rsp.split('_', 1)
                        if rsp[0] == "CONTINUE?":  # should happen around the 50% point of file transfer.
                            print("halfway done! continue?")
                            answer = "yes"
                            print("yes")  # CONTROL - TO BE REMOVED
                            if answer == "yes":
                                connection.sendto("CONTINUE".encode(), server_addr)
                            else:
                                self.set_response("Relaying Stop Message To Server")
                                self.set_res_flag(True)
                                connection.sendto("STOP".encode(), server_addr)
                                time.sleep(0.2)
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
        self.set_response("Received All Packets And Assembling Them To A File..")
        self.set_res_flag(True)
        time.sleep(0.15)

        with open("downloaded_" + fname, "ab") as file:
            for _ in packet_list:
                if _ is not None:  # even after RDT some packets may be missing - this is a precaution.
                    file.write(_)

        last_byte = str(bytearray(packet_list[-1])[-1])
        self.set_response("Last Byte Is "+ last_byte)
        self.set_res_flag(True)
        time.sleep(0.15)

    def handshakes(self, sock, addr) -> bool:
        for _ in range(0, 5):
            sock.sendto("HANDSHAKE".encode(), addr)
        time.sleep(1)
        res = ""
        addr = ""
        step2 = False  # step1 is on server side ( a similar code block )
        for _ in range(0, 5):
            try:
                temp1, temp2 = self.receive_message(sock)
                if temp1 == "TIMEOUT":
                    continue
                if not step2:
                    res = temp1
                    addr = temp2
                    step2 = True
            except IOError:
                continue
        if res == "" or addr == "":
            print("could not receive ACK back")
            return False

        if res[0] == "ACK":
            self.set_response("Server Is Live! Initializing Download..")
            self.set_res_flag(True)
            time.sleep(0.2)
        else:
            self.set_response("No Server Response...Please Try Again...")
            self.set_res_flag(True)
            time.sleep(0.2)
            return False

        for _ in range(0, 5):
            sock.sendto("ACK".encode(), addr)  # also completes the three-way handshake

        time.sleep(1)
        return True

    def UDP_Threader(self, filename, port) -> None:
        server_addr = (self.server_host, port)
        File_Socket = socket(AF_INET, SOCK_DGRAM)
        File_Socket.settimeout(60)
        File_Socket.connect(server_addr)

        self.set_response("Attempting To Confirm Connection With A Three-Way Handshake..")
        self.set_res_flag(True)
        time.sleep(0.5)

        if self.handshakes(File_Socket, server_addr):
            self.set_response("Three-Way Handshake Success!")
            self.set_res_flag(True)
            time.sleep(0.5)

            packets_len = ""
            step4 = False  # step3 is on client side ( a similar code block )
            for _ in range(0, 5):
                try:
                    temp1, _ = self.receive_message(File_Socket)
                    if not step4:
                        packets_len = temp1[1]
                        step4 = True
                except IOError or UnicodeDecodeError:
                    continue

            if packets_len == "":
                self.set_response("Server Timed Out! Couldn't Receive Amount of Packages")
                self.set_res_flag(True)
                time.sleep(0.5)
                return

            packet_list = [None] * int(packets_len)

            # ^ mirroring the list being sent from server - allows skipping re-ordering later
            self.set_response("Preparing to receive %s packages.." % packets_len)
            self.set_res_flag(True)
            time.sleep(0.5)

            self.file_receiver(File_Socket, server_addr, packet_list, filename)
        else:
            print("Could not complete three way handshake with the server! - try again")
        File_Socket.close()

        # ================================================================ #
        #                             END UDP                              #
        # ================================================================ #

    def TCP_Threader(self, fname, port):
        con = socket(AF_INET, SOCK_STREAM)
        con.bind(('', port))
        con.listen(5)

        c, addr = con.accept()

        location = os.path.realpath(os.getcwd())
        location = os.path.join(location, "Files")

        self.set_response("Receiving Request File via TCP...")
        self.set_res_flag(True)

        with open("downloaded" + fname, "ab") as file:
            packet = c.recv(self.MTU)
            while packet:
                file.write(packet)
                packet = c.recv(self.MTU)
        self.set_response("Received File Via TCP!!!")
        self.set_res_flag(True)
        time.sleep(0.5)
        con.close()

    def response_thread(self, client_socket):
        time.sleep(0.2)
        try:
            while self.running:
                rsp = client_socket.recv(8192)

                try:
                    rsp = pickle.loads(rsp)
                    protocol = rsp.pop()
                    if protocol == "FILES":
                        self.set_file_list(rsp)
                    if protocol == "USERS":
                        self.set_user_flag(True)
                        self.set_user_list(rsp)
                except pickle.PickleError or pickle.UnpicklingError:
                    rsp = rsp.decode()
                    rsp = rsp.split('_', 1)

                    if rsp == "TIMEOUT":
                        print("connection timed out")  # we do not expect a timeout here!
                        sys.exit(0)
                    if rsp[0] == "DCD":
                        self.running = False
                        print("Disconnected!")
                    if rsp[0] == "TCPFILE":
                        temp = rsp[1].split('_', 1)
                        port = temp[0]
                        fname = temp[1]
                        threading.Thread(target=self.TCP_Threader, args=[fname, int(port)]).start()
                    if rsp[0] == "FILE":
                        temp = rsp[1].split('_', 1)
                        port = temp[0]
                        fname = temp[1]
                        threading.Thread(target=self.UDP_Threader, args=[fname, int(port)]).start()
                    else:
                        self.set_response(rsp[0])
                        self.set_res_flag(True)
        except OSError:
            print("No Longer Receiving Messages")
            return

    def send_message(self, client_socket, message):
        try:
            checker = message.split('_', 1)
            if checker[0] == "DC":
                self.running = False

            # sending message regardless - protocol assurance should be done by controller!
            client_socket.send(message.encode())
        except OSError:
            self.set_response("Something Went Wrong With Sending The Message")
            self.set_res_flag(True)
            return

    def run(self):
        try:
            clientSocket = socket(AF_INET, SOCK_STREAM)
            self.set_TCP_Socket(clientSocket)
            print("Socket Created")
            clientSocket.connect((self.server_host, self.server_port))
            print("Connected to: " + self.server_host + " on port: " + str(self.server_port))
            clientSocket.send(self.username.encode())
            response = clientSocket.recv(8192)
            response = response.decode()
            response = response.split('_', 1)
            self.set_taken_flag(False)
            if response[0] == "TAKEN":
                self.set_taken_flag(True)
                print("username taken - try again!")
            else:
                threading.Thread(target=self.response_thread, args=(clientSocket,)).start()
        except IOError:
            print("An error has occurred, please try again\r\n Closing client connection")
            sys.exit(1)

