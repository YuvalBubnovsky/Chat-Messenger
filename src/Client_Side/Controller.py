import threading
import time
from tkinter import *
from tkinter import messagebox

from Server_Side import Client


class Controller:

    def __init__(self, root, chat_box, user_input, files_button, clear_button, user_list, send_button):
        self.client = Client.Client('127.0.0.1', 55000, 55001, " ", 1500, 5, True)
        self.root = root
        self.chat_box = chat_box
        self.user_input = user_input
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

    '''Updates GUI buttons in accordance to user state'''

    def update_state(self):
        for widget in [self.user_input, self.files_button, self.clear_button, self.user_list,
                       self.send_button]:
            if self.is_connected:
                widget.config(state=NORMAL)
            else:
                widget.config(state=DISABLED)

    '''Clears all writeable boxes in the GUI'''

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

    '''Threaded function to listen for server responses to print'''
    def write_chat(self):
        while True:
            if self.client.get_res_flag():
                self.chat_box.config(state=NORMAL)
                to_print = self.client.get_response()
                self.chat_box.insert('end', to_print + "\n")
                self.client.set_res_flag(False)  # Result Flag
                self.chat_box.see('end')
                self.chat_box.config(state=DISABLED)

            if self.client.get_user_flag():  # User connected/DCed flag
                lst = self.client.get_user_list()
                self.user_list.delete(0, 'end')
                for user in lst:
                    self.user_list.insert("end", user)
                self.client.set_user_flag(False)

    '''Function to write locally to a user'''
    def write_message(self, message: str):
        self.chat_box.config(state=NORMAL)
        self.chat_box.insert('end', message + "\n")
        self.chat_box.see('end')
        self.chat_box.config(state=DISABLED)

    '''Receive user name and address and inititate connection to server'''
    def connect(self, user_entry: Entry, addr_entry: Entry, login: Toplevel):
        user_name = user_entry.get()
        addr = addr_entry.get()
        self.client.set_server_host(addr)
        self.client.set_username(user_name)
        try:
            self.client.run()  # Client backend function to connect to server
        except OSError:
            messagebox.showinfo("Error!", "An Error Has Occured, Please Try Again!")
            return

        user_entry.delete(0, END)
        user_entry.insert(0, " ")
        addr_entry.delete(0, END)
        addr_entry.insert(0, " ")

        login.withdraw()  # Destroy our toplevel screen

        self.set_connected(True)  # Need this flag for control
        self.update_state()

        self.client.send_message(self.client.get_TCP_Socket(), "ALL_" + user_name + " Has Joined The Chat Room!")
        time.sleep(0.3)
        self.set_username(user_name)
        threading.Thread(target=self.write_chat, daemon=True).start()
        time.sleep(0.3)
        self.populate_user_list()
        time.sleep(0.3)
        self.populate_file_list()

        self.write_message("======================================")
        self.write_message("Welcome To The Chat Room!")
        self.write_message("To Write A Message To Everybody Else, Just Write Something And Press Enter!")
        self.write_message("To Write A PM, Double Click On User From The List")
        self.write_message("You Can Even PM Yourself! Enjoy!")
        self.write_message("======================================")

    '''Function to send messages to the actual server, uses our protocols'''
    def send_message(self):
        message = self.user_input.get()
        if "_" in message:  # If a message already has a protocol attached
            self.client.send_message(self.client.get_TCP_Socket(), message)
            self.user_input.delete(0, END)
        else:
            self.client.send_message(self.client.get_TCP_Socket(), "ALL_" + message)
            self.user_input.delete(0, END)

    '''Disconnect gracefully'''
    def disconnect(self):
        self.set_connected(False)
        self.update_state()
        self.client.send_message(self.client.get_TCP_Socket(), "ALL_" + self.get_username() + " Has Disconnected!")
        self.client.send_message(self.client.get_TCP_Socket(), "DC_disconnect")
        self.client.get_TCP_Socket().close()
        self.clear_all()

    '''Print file list locally to the user'''
    def show_file_list(self):
        file_lst = self.client.get_file_list()
        self.write_message("========== SERVER FILE LIST ==========")
        for file in file_lst:
            self.write_message(file)
        self.write_message("======================================")
        self.write_message("To download a file using UDP:")
        self.write_message("FILE_FILENAME.* (* is the format)")
        self.write_message("======================================")
        self.write_message("To download a file using TCP:")
        self.write_message("TCPFILE_FILENAME.*")
        self.write_message("============ END FILE LIST ===========")

    '''Send a private message'''
    def send_pm(self):
        cs = self.user_list.get(self.user_list.curselection())
        send_to = cs + "_"
        self.user_input.delete(0, "end")
        self.user_input.insert(0, send_to)

    def populate_user_list(self):
        self.client.send_message(self.client.get_TCP_Socket(), "GETUSERS_")  # Get user list

    def populate_file_list(self):
        self.client.send_message(self.client.get_TCP_Socket(), "WF_")  # Get file list
