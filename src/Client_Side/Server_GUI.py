from tkinter import *
from tkinter import messagebox


# Function to initiate proper shutdown if user exits through "X" button
# TODO: Add proper server teardown
def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()


# TODO: Implement functions below in MVC design pattern
def start():
    pass


def stop():
    pass


def print_log():
    # TODO: How to print to this?
    pass


# Root & Frame definition
root = Tk()
root.title("Server")
root.geometry("640x480")
root.resizable(width=False, height=False)
frame = Frame(root)
frame.pack()

# Menu bar and cascading menu items
menu_bar = Menu(frame)
main_menu = Menu(menu_bar, tearoff=False)
main_menu.add_command(label="Start Server", command=start)
main_menu.add_command(label="Shutdown Server", command=stop)
main_menu.add_command(label="Exit", command=root.destroy)
menu_bar.add_cascade(label="Menu", menu=main_menu)

# Text box & making it scrollable
scrollbar = Scrollbar(root)
scrollbar.pack(side=RIGHT, fill=Y)
text_box = Text(root, height=300, width=450)
text_box.insert("end-1c", "Test")  # TODO: remove this
text_box.pack()
text_box.config(yscrollcommand=scrollbar.set)
text_box.config(state=DISABLED)

# Final configuration and event loop
root.config(menu=menu_bar)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
