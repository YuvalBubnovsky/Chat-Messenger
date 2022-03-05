import os
import threading
import time
from tkinter import *
from tkinter import messagebox

from Server_Side import Client


class Controller:

    def __init__(self, root, chat_box, user_input, online_button, files_button, clear_button, user_list, send_button):
        self.client = Client.Client('127.0.0.1', 55000, 55001, " ", 1500, 5, True)
        # TODO: Is server needed?
        self.root = root
        self.chat_box = chat_box
        self.user_input = user_input
        self.online_button = online_button
        self.files_button = files_button
        self.clear_button = clear_button
        self.send_button = send_button
        self.user_list = user_list
        self.username = ""
        self.is_connected = False

    def set_root(self, new_root: Tk):
        self.root = new_root

    def set_chat_box(self, new_box: Text):
        self.chat_box = new_box

    def set_user_input(self, new_input):
        self.user_input = new_input

    def set_online_button(self, new_button: Button):
        self.online_button = new_button

    def set_files_button(self, new_button: Button):
        self.files_button = new_button

    def set_clear_button(self, new_button: Button):
        self.clear_button = new_button

    def set_send_button(self, new_button: Button):
        self.send_button = new_button

    def get_send_button(self):
        return self.send_button

    def set_user_list(self, new_list: Listbox):
        self.user_list = new_list

    def set_connected(self, new_status: bool):
        self.is_connected = new_status

    def get_connected(self):
        return self.is_connected

    def set_username(self, new_name: str):
        self.username = new_name

    def get_username(self):
        return self.username

    def update_state(self):
        for widget in [self.user_input, self.online_button, self.files_button, self.clear_button, self.user_list,
                       self.send_button]:
            if self.is_connected:
                widget.config(state=NORMAL)
            else:
                widget.config(state=DISABLED)

    def clear_all(self):
        self.chat_box.config(state=NORMAL)
        self.user_list.config(state=NORMAL)
        self.chat_box.delete("1.0", "end")
        self.user_list.delete(0, END)
        self.user_list.config(state=DISABLED)
        self.chat_box.config(state=DISABLED)

    def clear_text(self):
        self.chat_box.config(state=NORMAL)
        self.chat_box.delete("1.0", "end")
        self.chat_box.config(state=DISABLED)

    def write_chat(self):
        while True:
            if self.client.get_res_flag():
                self.chat_box.config(state=NORMAL)
                to_print = self.client.get_response()
                self.chat_box.insert('end',to_print+"\n")
                self.client.set_res_flag(False)
                self.chat_box.config(state=DISABLED)

    def write_message(self, message: str):
        self.chat_box.config(state=NORMAL)
        self.chat_box.insert('end', message + "\n")
        self.chat_box.config(state=DISABLED)

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
        user_entry.delete(0, END)
        user_entry.insert(0, " ")
        addr_entry.delete(0, END)
        addr_entry.insert(0, " ")
        login.withdraw()
        self.set_connected(True)
        self.update_state()
        self.client.send_message(self.client.get_TCP_Socket(), "ALL_" + user_name + " Has Joined The Chat Room!")
        self.set_username(user_name)
        threading.Thread(target=self.write_chat, daemon=True).start()

    def send_message(self):
        message = self.user_input.get()
        self.client.send_message(self.client.get_TCP_Socket(), message)
        self.user_input.delete(0, END)

    def disconnect(self):
        self.set_connected(False)
        self.update_state()
        self.client.send_message(self.client.get_TCP_Socket(), "ALL_" + self.get_username() + " Has Disconnected!")
        self.client.send_message(self.client.get_TCP_Socket(), "DC_disconnect")
        self.clear_all()

    def file_list(self) -> list:
        location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        location = os.path.join(location, "Files")
        location = os.fsencode(location)
        names_lst = []
        for file in os.listdir(location):
            filename = os.fsdecode(file)
            names_lst.append(filename)
            # print(filename, ": ", file)
        return names_lst

    # TODO: test the function below with proper enligh PC


'''
    def show_server_files(self):
        files = self.file_list()
        self.write_message("========= SERVER FILES =========\n")
        for file in files:
            self.write_message(file)
        self.write_message("================================")
'''
