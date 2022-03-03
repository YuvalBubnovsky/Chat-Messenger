from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Labelframe
import Controller

# TODO: Add DC functions

class Client_GUI:

    def __init__(self):
        self.root = Tk()
        self.root.title("Client")
        self.root.geometry("640x320")
        self.root.resizable(width=False, height=False)
        self.build_gui()
        self.controller = Controller.Controller(None, None)
        self.root.mainloop()

    # TODO: connect all functions to controller

    def build_gui(self):
        self.build_top_frame()
        self.build_mid_frame()
        self.build_bottom_frame()

    # Function to initiate proper shutdown if user exits through "X" button
    # TODO: add shutdown
    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.controller.disconnect()
            self.root.destroy()

    # def clear_text(self):  # For clearing user text-box after input
    #   self.delete(1.0, 'end')

    def on_login(self):
        login_screen = Toplevel(self.root)
        login_screen.title("Login")
        login_screen.geometry("300x250")

        username = StringVar()
        user_address = StringVar()

        # Set username label
        username_label = Label(login_screen, text="Username  ")
        username_label.place(relx=0.5, rely=0.2, anchor=CENTER)

        username_entry = Entry(login_screen, textvariable=username)
        username_entry.place(relx=0.5, rely=0.3, anchor=CENTER)

        address_label = Label(login_screen, text="Address  ")
        address_label.place(relx=0.5, rely=0.4, anchor=CENTER)

        address_entry = Entry(login_screen, textvariable=user_address, show='*')
        address_entry.place(relx=0.5, rely=0.5, anchor=CENTER)

        Label(login_screen, text="").pack()
        Button(login_screen, text="Connect", width=10, height=1,command= lambda: self.controller.connect(username_entry, address_entry, login_screen)).place(relx=0.5, rely=0.7, anchor=CENTER)

    def on_whois(self):
        pass

    def on_clear(self):
        pass

    def on_showfile(self):
        pass

    def build_top_frame(self):
        top_frame = Labelframe(self.root, text='Menu')
        top_frame.pack(padx=15)

        # TODO: Add state for button to switch once the user logged in and back out
        login_button = Button(top_frame, text="Login", width=10, command=self.on_login).pack(side='left', padx=5)

        # TODO: Add state for button to activate only once user logged in, same for show files
        show_online_button = Button(top_frame, text="Who's Online", width=10, command=self.on_whois, state=DISABLED).pack(
            side='left', padx=5)
        show_server_files_button = Button(top_frame, text="Show Files", width=10, command=self.on_showfile,
                                          state=DISABLED).pack(side='left', padx=5)
        clear_button = Button(top_frame, text="Clear", width=10, command=self.on_clear, state=DISABLED).pack(side='left',
                                                                                                        padx=5)

    def build_mid_frame(self):
        # TODO: How to print to this?
        chat_frame = Labelframe(self.root, text='Chat Box')
        chat_frame.pack(side='top', padx=15)

        display_box = Text(chat_frame, width=55, height=10)
        scrollbar = Scrollbar(chat_frame, command=display_box.yview, orient=VERTICAL)
        display_box.config(yscrollcommand=scrollbar.set)
        display_box.config(state=DISABLED)
        display_box.pack(side='left', padx=10)
        scrollbar.pack(side='left', fill='y')

        # TODO: populate list properly and bind double click functions
        user_list = Listbox(chat_frame, height=10, selectmode=SINGLE)
        user_list.pack(side='right', padx=5)

    def build_bottom_frame(self):
        bottom_frame = Labelframe(self.root, text='Enter Message')
        chat_area = Entry(bottom_frame, width=100, state=DISABLED)

        # TODO: add a bind for sending messages using return key
        chat_area.pack(side='top', pady=5)

        bottom_frame.pack(side='top')

        # TODO: add server shutdown functions to teardown for graceful exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)


if __name__ == '__main__':
    gui = Client_GUI()
