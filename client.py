import socket, threading, base64, os, json, time, csv
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

HOST = "127.0.0.1"
PORT = 55555

configFile = "sessionConfig.json"
chatHistoryFile = "chatHistory.csv"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

localMasterKey = None

def hashFunction(keyword, salt=None):
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000
    )

    hashed = kdf.derive(keyword.encode())
    return salt, hashed

def saveMasterPass(salt, hashedPass):
    configData ={
        "salt": salt.hex(),
        "hash": hashedPass.hex()
    }

    with open(configFile, "w") as file:
        json.dump(configData, file)
    
def loadMasterPass():
    if not os.path.exists(configFile):
        return None, None
    with open(configFile, "r") as file:
        configData = json.load(file)

    salt = bytes.fromhex(configData['salt'])
    storedHash = bytes.fromhex(configData['hash'])

    return salt, storedHash

def genKeyFromPass(password, alternateSalt = None):
    salt = alternateSalt if alternateSalt else b'StaticSalt123456'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000
    )

    derivedKey = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(derivedKey)

def logMessage(plainTextMsg):
    try:
        if localMasterKey:
            localCipher = Fernet(localMasterKey)
            encryptedLine = localCipher.encrypt(plainTextMsg.encode('utf-8')).decode()

            with open(chatHistoryFile, "a", newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), encryptedLine])
    except Exception as e:
        print(f"\n Failed to record history data: {e}")

def recieveMessages():
    while True:
        try:
            encryptedMessage = client.recv(1024)
            if encryptedMessage:
                try:
                    decodeCheck = encryptedMessage.decode('utf-8')
                    if decodeCheck == "YOU_HAVE_BEEN_KICKED":
                        print("\nYou have been removed from this room by the admin")
                        client.close()
                        os._exit(0)
                    elif decodeCheck.startswith("SERVER_ALERT:"):
                        print(f"\n {decodeCheck.replace('SERVER_ALERT:', '')}")
                        continue
                except UnicodeDecodeError:
                    pass
                decryptedMsg = fernetCipher.decrypt(encryptedMessage).decode('utf-8')
                print(decryptedMsg)

                logMessage(decryptedMsg)
            else:
                print("Disconnected: Connection to the server LOST :(")
                client.close()
                break
        except:
            print("Cryptographic error maybe - unexpected")
            client.close()
            break

def authentication():
    global localMasterKey
    print("--- Login ---")
    salt, storedHash = loadMasterPass()

    if salt is None and storedHash is None:
        print("Welcome to ChatPy! Set up a secure Master Password.")
        while True:
            newPass = input("Create Master Password: ")
            confirmPass = input("Confirm Master Password: ")

            if newPass == confirmPass:
                salt, storedHash = hashFunction(newPass)
                saveMasterPass(salt, storedHash)
                print("Client Profile Registered!\n")
                break
            else:
                print("Passwords does not match :(")
    
    tries = 0
    while True:
        if tries >= 3:
            print("Too Many failed attempts. Wait 30 seconds")
            time.sleep(30)
            tries = 0
        
        loginPass = input("Enter Master Password to unlock chat: ")
        _, attempHash = hashFunction(loginPass, salt)

        if attempHash == storedHash:
            print("--- Login Successful ---")
            localMasterKey = genKeyFromPass(loginPass, alternateSalt=salt)
            return True
        else:
            print("Login Failed. Please try again.")
            tries += 1

def sendMessages():
    print(f"Welcome {userName}! You can now start chatting :)\n")

    while True:
        try:
            userInput = input("")
            if userInput.strip():
                if userInput.startswith("/kick:"):
                    client.send(userInput.encode('utf-8'))
                else:
                    formatedMsg = f"{userName}: {userInput}"
                    encryptedMsg = fernetCipher.encrypt(formatedMsg.encode('utf-8'))
                    client.send(encryptedMsg)

                    logMessage(formatedMsg)
        except:
            print("ERROR: Failed to send message.")
            client.close()
            break
    
if __name__ == "__main__":

    if authentication():
        userName = str(input("Enter your username: ")).strip()
        targetRoom = str(input("Enter the Room Name to Create/Join: ")).strip().lower()
        roomPass = str(input("Enter the room Password: "))
        secretKey = genKeyFromPass(roomPass)

        fernetCipher = Fernet(secretKey)

        print("SUCCESS: Secure End-to-End Encrypted Chat Initialized")

        joinPacket = f"JOIN_ROOM:{targetRoom}:{userName}"
        client.send(joinPacket.encode('utf-8'))

        recieveThread = threading.Thread(target=recieveMessages)
        recieveThread.daemon = True
        recieveThread.start()

        sendMessages()