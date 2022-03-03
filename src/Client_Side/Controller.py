import threading
from tkinter import *
from tkinter import messagebox

from Server_Side import Client


class Controller:

    def __init__(self, chat_box, user_input, online_button, files_button, clear_button, user_list):
        self.client = Client.Client('127.0.0.1', 55000, 55001, " ", 1500, 5, True)
        # TODO: Is server needed?
        self.chat_box = chat_box
        self.user_input = user_input
        self.online_button = online_button
        self.files_button = files_button
        self.clear_button = clear_button
        self.user_list = user_list
        self.is_connected = False

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

    def set_user_list(self, new_list: Listbox):
        self.user_list = new_list

    def update_state(self):
        for widget in [self.user_input, self.online_button, self.files_button, self.clear_button, self.user_list]:
            if self.is_connected:
                widget.config(state=NORMAL)
            else:
                widget.config(state=DISABLED)

    def clear_all(self):
        self.chat_box.config(state=NORMAL)
        self.user_list.config(state=NORMAL)
        self.chat_box.delete("1.0", "end")
        self.user_list.delete(0,END)
        self.user_list.config(state=DISABLED)
        self.chat_box.config(state=DISABLED)

    def clear_text(self):
        self.chat_box.config(state=NORMAL)
        self.chat_box.delete("1.0", "end")
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
        self.is_connected = True
        self.update_state()
        self.chat_box.config(state=NORMAL)
        self.chat_box.insert('end', "Connected To Server!")
        self.chat_box.config(state=DISABLED)

    def disconnect(self):
        self.update_state()
        self.clear_all()
        pass  # TODO: Implement this with the state button of login/logout
