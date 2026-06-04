import socket, threading

HOST = "127.0.0.1"
PORT = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

rooms = {}

clientUsernames = {}

def broadCastMessage(message, senderClient, roomName):
    if roomName in rooms:
        for client in rooms[roomName]["members"]:
            if client != senderClient:
                try:
                    client.send(message)
                except:
                    removeClient(client, roomName)

def handleClient(client, roomName):
    while True:
        try:
            message = client.recv(1024)
            if message:
                try:
                    decodedMsg = message.decode('utf-8')

                    if decodedMsg.startswith("/kick:"):
                        if rooms[roomName]["admin"] == client:
                            targetUser = decodedMsg.split(":")[1].strip().lower()
                            kickStatus = False

                            for memberSocket in list(rooms[roomName]['members']):
                                if clientUsernames.get(memberSocket, "").lower() == targetUser:
                                    try: 
                                        memberSocket.send("YOU_HAVE_BEEN_KICKED".encode('utf-8'))
                                    except:
                                        pass

                                    removeClient(memberSocket, roomName)
                                    kickStatus = True
                                    break
                            if kickStatus:
                                print(f"Admin kicked {targetUser} from room {roomName}")
                                alertPacket = f"SERVER_ALERT: {targetUser.capitalize()} was kicked by the Admin"
                                broadCastMessage(alertPacket.encode('utf-8'), client, roomName)
                        else:
                            client.send("SERVER_ALERT: Access Denied! You are not the room Admin")
                    continue
                except UnicodeDecodeError:
                    pass
                
                print(f"{roomName.upper()} routing message !")
                broadCastMessage(message, client, roomName)
            else:
                removeClient(client, roomName)
                break
        except:
            removeClient(client, roomName)
            break

def removeClient(client, roomName):
    if roomName in rooms and client in rooms[roomName]["members"]:
        rooms[roomName]["members"].remove(client)

        userName = clientUsernames.get(client, "A user")
        client.close()

        if client in clientUsernames:
            del clientUsernames[client]
        
        print(f"Disconnected: Cleared Socket from Room: {roomName}")

        if rooms[roomName]["admin"] == client:
            if rooms[roomName]["members"]:
                rooms[roomName]["admin"] = rooms[roomName]["members"][0]
                newAdminName = clientUsernames.get(rooms[roomName]["admin"], "Next User")

                alert = f"SERVER_ALERT: Admin Left. {newAdminName} is now the Admin"
                broadCastMessage(alert.encode('utf-8'), None, roomName)
            else:
                del rooms[roomName]
                print(f"Room {roomName} is empty and has been deleted")
            
def recieveConnections():
    print(f"STARTING: Server is listening at {HOST}:{PORT}")
    while True:
        clientSocket, address = server.accept()
        print(f"CONNECTED: New connection established from {str(address)}")

        try:
            initMsg = clientSocket.recv(1024).decode('utf-8')

            if initMsg.startswith("JOIN_ROOM"):
                parts = initMsg.split(":")
                roomName = parts[1].strip().lower()
                userName = parts[2].strip()

                if roomName not in rooms:
                    rooms[roomName] = {
                        "admin": clientSocket,
                        "members": []
                    }

                    print(f"SERVER_ALERT: Room {roomName} created. Admin assigned: {userName}")
                    clientSocket.send("SERVER_ALERT: You created this room and you are the admin! Use /kick:username to remove members".encode('utf-8'))
                else:
                    clientSocket.send(f"SERVER_ALERT: Joined Room {roomName} successfully".encode('utf-8'))
                
                rooms[roomName]["members"].append(clientSocket)
                print(f"{userName} mapped to room: {roomName}")
                
                thread = threading.Thread(target=handleClient, args=(clientSocket, roomName,))
                thread.start()
            else:
                clientSocket.close()
        except:
            clientSocket.close()

if __name__ == "__main__":
    recieveConnections()