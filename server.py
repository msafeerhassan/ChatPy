import socket, threading

HOST = "127.0.0.1"
PORT = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

rooms = {}

def broadCastMessage(message, senderClient, roomName):
    if roomName in rooms:
        for client in rooms[roomName]:
            if client != senderClient:
                try:
                    client.send(message)
                except:
                    removeClient(client)

def handleClient(client, roomName):
    while True:
        try:
            message = client.recv(1024)
            if message:
                print(f"{roomName.upper()} Routing message!")
                broadCastMessage(message, client, roomName)
            else:
                removeClient(client, roomName)
                break
        except:
            removeClient(client, roomName)
            break

def removeClient(client, roomName):
    if roomName in rooms and client in rooms[roomName]:
        rooms[roomName].remove(client)
        client.close()
        print(f"DISCONNECTED: Cleared Socket from Room: {roomName}")

def recieveConnections():
    print(f"STARTING: Server is listening at {HOST}:{PORT}")
    while True:
        clientSocket, address = server.accept()
        print(f"CONNECTED: New connection established from {str(address)}")

        try:
            initMsg = clientSocket.recv(1024).decode('utf-8')

            if initMsg.startswith("JOIN_ROOM"):
                roomName = initMsg.split(":")[1].strip().lower()

                if roomName not in rooms:
                    rooms[roomName] = []
                
                rooms[roomName].append(clientSocket)
                print(f"ASSIGNED: Socket mapped to room: {roomName}")

                thread = threading.Thread(target=handleClient, args=(clientSocket, roomName))
                thread.start()
            else:
                clientSocket.close()
        except:
            clientSocket.close()

if __name__ == "__main__":
    recieveConnections()