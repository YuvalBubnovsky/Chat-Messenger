from glob import glob
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Labelframe

root = Tk()
root.title("Client")
root.geometry("640x320")
root.resizable(width=False, height=False)


# TODO: Switch all functions to lambda functions
# TODO: Add a function to switch the listbox from usernames to files and back - optional

######################################
#                                    #
#        GLOBAL FUNCTIONS            #
#                                    #
######################################

# Function to initiate proper shutdown if user exits through "X" button
# TODO: add shutdown
def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()


def clear_text(self):  # For clearing user text-box after input
    self.delete(1.0, 'end')


# TODO: Implement functions below using MVC design pattern
def on_login():
    login_screen = Toplevel(root)
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
    Button(login_screen, text="Connect", width=10, height=1).place(relx=0.5, rely=0.7, anchor=CENTER)


def on_whois():
    pass


def on_clear():
    pass


def on_showfile():
    pass


######################################
#                                    #
#           TOP FRAME                #
#                                    #
######################################

top_frame = Labelframe(root, text='Menu')
top_frame.pack(padx=15)

# TODO: Add state for button to switch once the user logged in and back out
login_button = Button(top_frame, text="Login", width=10, command=on_login).pack(side='left', padx=5)

# TODO: Optional - switch these to a popup dialog once the login button is pressed
Label(top_frame, text='Name:').pack(side='left', padx=10)
name = Entry(top_frame, width=10, borderwidth=2)
name.pack(side='left', anchor='e')
Label(top_frame, text='Address:').pack(side='left', padx=10)
address = Entry(top_frame, width=10, borderwidth=2)
address.pack(side='left', anchor='e')

# TODO: Add state for button to activate only once user logged in, same for show files
show_online_button = Button(top_frame, text="Who's Online", width=10, command=on_whois).pack(side='left', padx=5)
show_server_files_button = Button(top_frame, text="Show Files", width=10, command=on_showfile).pack(side='left', padx=5)
clear_button = Button(top_frame, text="Clear", width=10, command=on_clear).pack(side='left', padx=5)

######################################
#                                    #
#           MID FRAME                #
#                                    #
######################################

# TODO: How to print to this?
chat_frame = Labelframe(root, text='Chat Box')
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

######################################
#                                    #
#           BOTTOM FRAME             #
#                                    #
######################################

bottom_frame = Labelframe(root, text='Enter Message')
chat_area = Text(bottom_frame, width=75, height=2)

# TODO: add a bind for sending messages using return key
chat_area.pack(side='top', pady=5)

bottom_frame.pack(side='top')

# TODO: add server shutdown functions to teardown for graceful exit
root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
