import socket, threading, base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

HOST = "127.0.0.1"
PORT = 55555

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

def genKeyFromPass(password):
    salt = b'StaticSalt123456'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000
    )

    derivedKey = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(derivedKey)

def recieveMessages():
    while True:
        try:
            encryptedMessage = client.recv(1024)
            if encryptedMessage:
                decryptedMessage = fernetCipher.decrypt(encryptedMessage).decode('utf-8')
                print(decryptedMessage)
            else:
                print("DISCONNECTED: Connection to Server LOST!")
                client.close()
                break
        except:
            print("ERROR: An error occured while recieving messages. Please enter correct Room Password")
            client.close()
            break

def sendMessages():
    userName = str(input("Enter your username: "))
    # roomPass = str(input("Enter the room Password: "))
    print(f"Welcome {userName}! You can now start chatting :)\n")

    while True:
        try:
            userInput = input("")
            if userInput.strip():
                formatedMsg = f"{userName}: {userInput}"
                encryptedMsg = fernetCipher.encrypt(formatedMsg.encode('utf-8'))
                client.send(encryptedMsg)
        except:
            print("ERROR: Failed to send message.")
            client.close()
            break
    
if __name__ == "__main__":
    targetRoom = str(input("Enter the Room Name to Create/Join: ")).strip().lower()

    roomPass = str(input("Enter the room Password: "))
    secretKey = genKeyFromPass(roomPass)

    fernetCipher = Fernet(secretKey)

    print("SUCCESS: Secure End-to-End Encrypted Chat Initialized")

    joinPacket = f"JOIN_ROOM:{targetRoom}"
    client.send(joinPacket.encode('utf-8'))

    recieveThread = threading.Thread(target=recieveMessages)
    recieveThread.daemon = True
    recieveThread.start()

    sendMessages()