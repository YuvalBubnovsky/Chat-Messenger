from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Labelframe
import Controller


class Client_GUI:

    '''GUI Window initialization'''
    def __init__(self):
        self.root = Tk()
        self.root.title("Client")
        self.root.geometry("640x320")
        self.root.resizable(width=False, height=False)
        # Passing NONE arguments to controller to be set later
        self.controller = Controller.Controller(None, None, None, None, None, None, None)
        self.build_gui()
        self.controller.set_root(self.root)
        # Standard TKinter shutdown protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    '''Uses built-in frame building functions to put everything together and display'''
    def build_gui(self):
        self.build_top_frame()
        self.build_mid_frame()
        self.build_bottom_frame()

    '''Function to initiate proper shutdown if user exits through "X" button'''
    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.controller.get_connected():
                self.controller.disconnect()
            self.root.destroy()

    '''Takes in user input and connects/disconnects from the server'''
    def on_login(self, button: Button):
        if button.cget('text') == "Login":
            button.config(text="Logout")
            login_screen = Toplevel(self.root)
            login_screen.title("Login")
            login_screen.geometry("300x250")

            username = StringVar()
            user_address = StringVar()

            username_label = Label(login_screen, text="Username  ")
            username_label.place(relx=0.5, rely=0.2, anchor=CENTER)

            username_entry = Entry(login_screen, textvariable=username)
            username_entry.place(relx=0.5, rely=0.3, anchor=CENTER)

            address_label = Label(login_screen, text="Address  ")
            address_label.place(relx=0.5, rely=0.4, anchor=CENTER)

            address_entry = Entry(login_screen, textvariable=user_address)
            address_entry.place(relx=0.5, rely=0.5, anchor=CENTER)

            Label(login_screen, text="").pack()
            Button(login_screen, text="Connect", width=10, height=1,
                   command=lambda: self.controller.connect(username_entry, address_entry, login_screen)).place(relx=0.5,
                                                                                                               rely=0.7,
                                                                                                               anchor=CENTER)
        else:
            button.config(text="Login")
            self.controller.disconnect()

    '''Builds top frame for GUI'''
    def build_top_frame(self):
        top_frame = Labelframe(self.root, text='Menu')
        top_frame.pack(padx=15)

        login_button = Button(top_frame, text="Login", width=10,
                              command=lambda: self.on_login(login_button))
        login_button.pack(side='left', padx=5)

        show_server_files_button = Button(top_frame, text="Show Files", width=10,
                                          command=self.controller.show_file_list, state=DISABLED)
        show_server_files_button.pack(side='left', padx=5)
        self.controller.set_files_button(show_server_files_button)

        clear_button = Button(top_frame, text="Clear", width=10, command=self.controller.clear_text,
                              state=DISABLED)
        clear_button.pack(side='left', padx=5)
        self.controller.set_clear_button(clear_button)

    '''Builds middle frame for GUI'''
    def build_mid_frame(self):
        chat_frame = Labelframe(self.root, text='Chat Box')
        chat_frame.pack(side='top', padx=15)

        display_box = Text(chat_frame, width=55, height=10)
        scrollbar = Scrollbar(chat_frame, command=display_box.yview, orient=VERTICAL)
        display_box.config(yscrollcommand=scrollbar.set)
        display_box.config(state=DISABLED)
        display_box.pack(side='left', padx=10)
        scrollbar.pack(side='left', fill='y')
        self.controller.set_chat_box(display_box)

        user_list = Listbox(chat_frame, height=10, selectmode=SINGLE)
        user_list.pack(side='right', padx=5)
        user_list.bind('<Double-1>', lambda event: self.controller.send_pm())
        self.controller.set_user_list(user_list)

    '''Builds bottom frame for GUI'''
    def build_bottom_frame(self):
        bottom_frame = Labelframe(self.root, text='Enter Message')
        chat_area = Entry(bottom_frame, width=84, state=DISABLED)

        chat_area.pack(side='left', pady=5)
        send_button = Button(bottom_frame, text="Send", width=10, command=lambda: self.controller.send_message(),
                             state=DISABLED)
        chat_area.bind('<Return>', lambda event: self.controller.send_message())
        send_button.pack(side='right', anchor='e', padx=10)
        self.controller.set_send_button(send_button)

        self.controller.set_user_input(chat_area)

        bottom_frame.pack(side='top')


if __name__ == '__main__':
    gui = Client_GUI()
