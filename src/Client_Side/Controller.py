import threading
from tkinter import *

from Server_Side import Client, Server

class Controller:

    def __init__(self, addr, chat_box, users_box):
        self.client = Client()
        self.server = Server() # TODO: this will not be a class eventually
        self.addr = addr
        self.chat_box = chat_box
        self.users_box = users_box
        self.recv_thread = threading.Thread(target=self.recv, args=(chat_box), daemon=True)
        self.recv_flag = True
        self.chat_box = chat_box

    def recv(self, chat_box: Text, users_box: Listbox):
        while self.recv_flag:
            try:



