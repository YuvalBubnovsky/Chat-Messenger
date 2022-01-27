import sys
from socket import *
from threading import *

PING_PORT = 50000  # port that handles initial connection

allocating_socket = socket(AF_INET, SOCK_STREAM)
allocating_socket.listen(15)  # we allow 15 connections max, so at worst we will need to multi-thread 15 requests.

taken_ports = {False, False, False, False, False, False, False, False, False, False, False, False, False, False, False}


