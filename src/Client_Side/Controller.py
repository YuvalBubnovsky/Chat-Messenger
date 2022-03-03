import threading
from tkinter import *
from tkinter import messagebox

from Server_Side import Client


class Controller:

    def __init__(self, chat_box, user_input):
        self.client = Client.Client('127.0.0.1', 55000, 55001, " ", 1500, 5, True)
        # TODO: Is server needed?
        self.chat_box = chat_box
        self.user_input = user_input

    def set_chat_box(self, new_box: Text):
        self.chat_box = new_box

    def set_user_input(self, new_input):
        self.user_input = new_input


    def connect(self, user_entry: Entry, addr_entry: Entry, login: Toplevel):
        user_name = user_entry.get()
        addr = addr_entry.get()
        self.client.set_server_host(addr)
        self.client.set_username(user_name)
        try:
            self.client.run()
        except OSError:
            messagebox.showinfo("Error!", "An Error Has Occured, Please Try Again!")
            return
        user_entry.delete(0,END)
        user_entry.insert(0, " ")
        addr_entry.delete(0,END)
        addr_entry.insert(0, " ")
        login.withdraw()

    def disconnect(self):
        pass # TODO: Implement this with the state button of login/logout








