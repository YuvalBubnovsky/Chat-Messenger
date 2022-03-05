import os
import threading
import unittest
from socket import *
from Common import *


def test_thread_sender_udp(sock, addr):
    sock.connect(('127.0.0.1', 60000))
    index = 0
    sock.sendto(str(index).encode(), addr)
    index += 1
    response = sock.recv(8192).decode()
    print(response)
    sock.sendto(str(index).encode(), addr)
    index += 1
    response = sock.recv(8192).decode()
    print(response)
    sock.sendto(str(index).encode(), addr)
    index += 1
    response = sock.recv(8192).decode()
    print(response)
    sock.close()


def test_thread_receiver_udp(sock, addr):
    message, addr = sock.recvfrom(8192)
    sock.sendto(message, addr)
    message, addr = sock.recvfrom(8192)
    sock.sendto(message, addr)
    message, addr = sock.recvfrom(8192)
    sock.sendto(message, addr)
    sock.close()


def test_thread_sender_tcp(sock, addr):
    sock.connect(('127.0.0.1', 60001))
    index = 0
    sock.send(str(index).encode())
    index += 1
    response = sock.recv(8192).decode()
    print(response)
    sock.send(str(index).encode())
    index += 1
    response = sock.recv(8192).decode()
    print(response)
    sock.send(str(index).encode())
    index += 1
    response = sock.recv(8192).decode()
    print(response)
    sock.close()


def test_thread_receiver_tcp(sock, addr):
    sock, adr = sock.accept()
    message = sock.recv(8192)
    sock.send(message)
    message = sock.recv(8192)
    sock.send(message)
    message = sock.recv(8192)
    sock.send(message)
    sock.close()


class MyTestCase(unittest.TestCase):

    def test_checksum(self):
        packet = "TEST#".encode()
        self.assertTrue(17987 == calc_checksum(packet))

    def test_transform_packet(self):
        seq_num = 0
        packet = "TEST".encode()
        checksum = calc_checksum(packet)
        cwnd = 1
        transformed_packet = transform_packet(seq_num, checksum, packet, cwnd)
        new_tuple, new_packet = unpack_transformed_packet(transformed_packet)
        new_num = new_tuple[0]
        new_sum = new_tuple[1]
        new_window = new_tuple[2]
        self.assertTrue(new_num == seq_num)
        self.assertTrue(new_sum == checksum)
        self.assertTrue(calc_checksum(new_packet) == checksum)
        self.assertTrue(new_window == cwnd)
        self.assertTrue(packet.decode() == new_packet.decode())

    def test_simultaneous_messages(self):
        # the idea is to see this in action - and for it to not crash.
        # it simply sends 0 then 1 then 2 and expects to receive them in the same order.
        # that is send - receive - send - receive - send - receive
        try:
            udp_sock_1 = socket(AF_INET, SOCK_DGRAM)
            udp_sock_1.bind(('127.0.0.1', 60000))
            threading.Thread(daemon=True, target=test_thread_receiver_udp, args=[udp_sock_1, ('127.0.0.1', 60000)])\
                .start()
            udp_sock_2 = socket(AF_INET, SOCK_DGRAM)
            threading.Thread(daemon=True, target=test_thread_sender_udp, args=[udp_sock_2, ('127.0.0.1', 60000)])\
                .start()

            tcp_sock_1 = socket(AF_INET, SOCK_STREAM)
            tcp_sock_1.bind(('127.0.0.1', 60001))
            tcp_sock_1.listen()
            threading.Thread(daemon=True, target=test_thread_receiver_tcp, args=[tcp_sock_1, ('127.0.0.1', 60001)])\
                .start()

            tcp_sock_2 = socket(AF_INET, SOCK_STREAM)
            threading.Thread(daemon=True, target=test_thread_sender_tcp, args=[tcp_sock_2, ('127.0.0.1', 60001)])\
                .start()
        except IOError or UnicodeDecodeError:
            self.fail()
        finally:
            self.assertTrue(True)

    def test_file_reading(self):
        location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        location = os.path.join(location, "Files")
        index = 0
        with open(os.path.join(location, "Heavy.jpg"), "rb") as file:
            while _ := file.read(1500):
                index += 1
        self.assertTrue(index == 116)
        # "Heavy.jpg" weighs 168kb - 172,777 bytes to be precise, and thus we expect 172,777/1500 = 115 + 1
        # ( due to leftover ) packets of size 1500 each.


if __name__ == '__main__':
    unittest.main()
