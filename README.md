# Python Messenger App
>Made by: [Yuval Bubnovsky](https://github.com/YuvalBubnovsky) & [Yonatan Ratner](https://github.com/Teklar223)

This messenger app is the final assignment in our Computer-Networking course, Ariel University, 2021.

## How To use
1. navigate to backend using your cd command (pycharm terminal)
2. now enter ```python Server.py``` and it should boot
3. next you can launch the Client_GUI, pick any username and in address write ``` 127.0.0.1 ```

- if you cannot open multiple edit your run configurations: </br>
![image](https://user-images.githubusercontent.com/73063105/156900076-70a6ff2c-caf6-4a46-9694-29f36aded08a.png)
- and make sure this box is checked: </br>
![image](https://user-images.githubusercontent.com/73063105/156900109-c3d7144d-815b-4803-81aa-7701f832a429.png)

## Introduction:
This is an exercise in networking and communications, therefore it is expected that if we are asked to write ac chat app it would be using sockets to communicate messages – rather than a standard library like we can see in web development nowadays, and in this exercise we had to learn to manage multiple connections on the same machine using threads, create a protocol language, and devise algorithms to transfer files in a dependable manner.

## Approach:
The project is quite large and undoubtedly complicated at certain code blocks – therefore we will be cutting up the explanation, it is important to note that the code is mostly object oriented, and is built upon two important parts, the client and the server.</br></br>
At first we built two scripts, server and client, that will serve as a ‘skeleton’ for the communications, we implemented basic protocols for chat and files and used the terminal to communicate these requests until it was ready to be integrated with a GUI interface, at which point Client was changed to be an object class rather than a script and a Controller was added to implement MVC pattern.

### Protocol 
Before everything else, we had to devise a way for the clients and server to communicate their requests to each other and separate those requests to different threads and methods while the communication remains on the same line, we ended up with a basic solution – every message being sent is divided into two parts, like so: Protocol_Message. </br></br>
We used the split method that python provides to split just the first ‘_’ character – thus being able to send any message with any protocol we want, this was complicated at first but eventually simplified client to server and server to client communications and allows the client and server to operate as two separate entities.

### Server 
Firstly, the server is boot and play – there is no ‘admin’ interaction, such that it is only a process with a terminal that displays some logs ( for our usage, and not meant for the clients ), this means that the server is a standalone service provider meant for clients to interact with and make requests upon, the server is always listening to connections and once it receives a new connection from a client it checks if his username is taken, and proceeds accordingly while sending him a protocol message that verifies his connection or tells him to make a new username. </br></br>
Once he has found a username that is not taken, the server saves his connection information and username to be used later and then opens a new thread for that user to always listen to his request, as long as that user is connected.</br></br>
If for some reason the client disconnects, either through the appropriate protocol, or if that message does not arrive – the server knows to remove the client without extra work on the clients side.</br></br>
The server also has a Files folder and 2 dedicated threads to manage file transfer to the client upon request
 
### Client
This is the interactable part of the project, the Client can boot this up and attempt to connect to the server, naturally if it’s offline this will fail, once the client enters which address to connect to and his username he will be connected to the server, if that username is taken, he will need try again.</br>
Once a connection is successful, the client can interact with the server and other clients in different ways, there is a way to send a message to the chat, or alternatively to a specific client as a PM – a private message. </br></br>
There is also a way to download files from the server, with an option for either TCP or Reliable UDP ways to download these files simultaneously to other clients also downloading the same files

### Chat
In order to accomplish sending messages to the chat room / a private user, we first had to create appropriate protocols for this type of request and then in the server separate this into two different methods appropriately. </br></br>
Sending messages to everyone is done by a broadcast to all, which uses the saved connection information of every client, and iterates over it to send the message to all the connected users. </br></br>
Sending a message to just one person requires him to be online and is achieved by finding him using his unique username in the saved client information, and sending the message only to him with a distinct PM-messagingUser tag. </br></br>

### Files
Currently the server has 5 files of varying sizes – the smallest weighing 70kb and the largest weighing 64.6mb, which can be transferred through TCP or Reliable UDP simultaneously and by several clients and can support ANY type of file that we add, currently we have tested this with .txt .png .mp3 and .mp4 files, that is in order – text, images, sound, and video files. </br></br>
How it works – the user submits a request to the server to tell him what files are available – he then chooses one and a transfer method, TCP or UDP, after which a new connection is secured and threaded separately to the other processes already in action. </br></br>
The transfer itself is a breaking of the file into segments of 1500 bytes to minimize IP fragmentation, and sending them over the established connection, where on the other side it is received and written to a file. </br></br>
For the TCP segment this is done extremely naively – as the protocol itself makes sure our packets arrive safely. </br></br>
On other hand the UDP was required to be reliable, therefore we implemented what is often referred to as TCP over UDP, that means that we implemented a reliable data transfer and congestion control in the application layer rather then the transport layer, this means things like a three-way-handshake, rolling window, and selective repeat. </br>
These are important processes that insure a packet has arrived safely and reliably for the entire file: </br></br>
A three way handshake is a way for the client and user to attempt to establish a connection, it is a short process of requests and communications to confirm the connection.
Selective Repeat is a method that sends only packets that were not acknowledged by the client for any reason, and resends those. </br></br>
A window is the amount of packets being sent by the selective repeat process, and a rolling window means that we keep moving it to the next segment of packets in a serial manner. </br></br>
As for CC it only changes the window size, seeing as we are only sending packets of 1500bytes every time.

### GUI

The design pattern our GUI is MVC (Model – view – Controller) where the Client-server backend logic is the model, the Client_GUI class is the view, and the controller is self-explanatory.</br></br>
The Client_GUI & Controller classes are designed as objects to simplify their relationship, where the Controller communicates with both the frontend/backed and implements user input to the program, this MVC design allowed us to “separate” the actual program logic from what the user sees.</br></br>
We used Python’s TKinter library for our GUI, and when it starts, a TKinter window is created with an instance of a Controller inside, the same Controller has an instance of a Client within it, this design allows us to implement MVC, user input is performed using the GUI and sent to the controller, which applies the relevant functions according to the input.

### Unit-testing
Seeing as most if not all our code is just an assortment of different methods coming together, we set out to make sure we understand the methods we use and can reproduce them when needed, as such these tests don’t directly test any method, we built but rather test their foundations, like creating sockets and sending messages between them, or calculating checksum and using struct to alter packets. </br></br>
This implies a strong foundation for our code and allows us to be sure that the more complex methods within are based on correct ways of working with these libraries.</br></br>
For these ‘more complex’ methods we did not revise a test, seeing as it would require essentially writing the same method again, instead we tested it rigorously and often by hand.</br></br>
for example, sending files over UDP is the biggest method we built, and we tested it by activating the method and seeing that we indeed got a correct file transfer.

## Sequence Diagram
![image](https://user-images.githubusercontent.com/73063105/156900386-1cc0dab6-5bd1-4869-ab0a-6f036d498e81.png)

## Hierarchy
![image](https://user-images.githubusercontent.com/73063105/156900396-b5c749b6-ab26-4470-a43c-ca79243984f4.png)

## Links
sending lists as a stream of bytes - https://docs.python.org/3/library/pickle.html </br>
simulating packet loss on windows - https://github.com/jagt/clumsy
