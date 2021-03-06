import structures as st
import random
import sys, traceback
import socket
import pickle
import os

X_A = None
SESSION_KEY = None

def closeConnection(conn):
    header = st.Header(st.EXIT, myIP, serverIP)
    reqMsgObj = st.Message()
    reqMsgObj.header = header
    reqMsg = pickle.dumps(reqMsgObj)
    conn.send(reqMsg)
    conn.close()

def establiishKey(conn, myIP, serverIP):
    global SESSION_KEY
    Y_A = pow(st.alpha, X_A, st.prime)
    
    header = st.Header(st.KEYESTAB, myIP, serverIP)
    reqMsgObj = st.Message()
    reqMsgObj.header = header
    reqMsgObj.dummy = Y_A
    
    # Serializing object into ByteString
    reqMsg = pickle.dumps(reqMsgObj)
    conn.send(reqMsg)
    
    # Deserializing received string into object
    replyMsg= conn.recv(st.MAX_LEN)
    replyMsgObj = pickle.loads(replyMsg)

    if replyMsgObj.status == st.SUCCESSFUL:
        Y_B = replyMsgObj.dummy
        SESSION_KEY = pow(Y_B, X_A, st.prime)
        print("Session key sucessfully established and is: ", SESSION_KEY)
        return True
    else:
        print("Unable to setup session key as Y_B not supplied by server..")
        # Needs to close the connection at the server
        # conn.close()
        closeConnection(conn)
        quit()
    return False


def loginCreate(conn, myIP, serverIP):
    # Later all the valid fields of Message object needs to be encrypted using the already established key between this client and server -- ToDo
    id = input("Enter the client's ID: ")
    password = input("Enter the client's password: ")
    
    header = st.Header(st.LOGINCREAT, myIP, serverIP)
    reqMsgObj = st.Message()
    reqMsgObj.header = header
    reqMsgObj.id = id
    reqMsgObj.password = password
    reqMsgObj.q = st.prime

    print("Sending message object before encryption is:\n")
    st.printMessage(reqMsgObj)

    # First Message needs to be encrypted -- ToDo
    # do not encrypt header    
    reqMsgObj = st.encryptMessageObj(SESSION_KEY, reqMsgObj)

    print("Sending message object after encryption is:\n")
    st.printMessage(reqMsgObj)

    reqMsg = pickle.dumps(reqMsgObj)
    # print("Sending encrypted pickle is: ", reqMsg)
    conn.send(reqMsg)

    replyMsg = conn.recv(st.MAX_LEN)
    replyMsgObj = pickle.loads(replyMsg)

    # Now the reply Meaasge and header needs to be decrypted -- ToDo
    replyMsgObj = st.decryptMessageObj(SESSION_KEY, replyMsgObj)

    if replyMsgObj.status == st.SUCCESSFUL:
        print("Client successfully registered at server..")
        return True
    else:
        print("Error occurred while registering client at server..")
        # Needs to close the connection at the server
        # conn.close()
        closeConnection(conn)
        quit()
    return False


def authenticate(conn, myIP, serverIP):
    id = input("Enter the this client's ID: ")
    password = input("Enter the client's password: ")
    
    header = st.Header(st.AUTHREQUEST, myIP, serverIP)
    reqMsgObj = st.Message()
    reqMsgObj.header = header
    reqMsgObj.id = id
    reqMsgObj.password = password
    reqMsgObj.q = st.prime

    # First Message needs to be encrypted -- ToDo
    # do not encrypt header
    reqMsgObj = st.encryptMessageObj(SESSION_KEY, reqMsgObj)

    reqMsg = pickle.dumps(reqMsgObj)
    conn.send(reqMsg)

    replyMsg = conn.recv(st.MAX_LEN)
    replyMsgObj = pickle.loads(replyMsg)

    # Now the reply Meaasge and header needs to be decrypted -- ToDo
    replyMsgObj = st.decryptMessageObj(SESSION_KEY, replyMsgObj)
    
    if replyMsgObj.status == st.SUCCESSFUL:
        print("Client successfully authenticated at server..")
        return True
    else:
        print("Error occurred while authenticating client at server..")
        # Needs to close the connection at the server
        # conn.close()
        # closeConnection(conn)
        # quit()
    return False


def downloadFile(conn, myIP, serverIP):

    fileName = input("Enter the file name to be downloaded: ")
    header = st.Header(st.SERVICEREQUEST, myIP, serverIP)
    reqMsgObj = st.Message()
    reqMsgObj.header = header
    reqMsgObj.file = fileName

    # First Message needs to be encrypted -- ToDo
    # do not encrypt header
    reqMsgObj = st.encryptMessageObj(SESSION_KEY, reqMsgObj)

    reqMsg = pickle.dumps(reqMsgObj)
    conn.send(reqMsg)

    try:
        filePath = "downloads/" + fileName
        filePtr = open(filePath, "w")
    except IOError:
        print("Unable to open file: ", fileName)
        return
        # closeConnection(conn)
    
    # File opened successfully
    try:
        replyMsg = conn.recv(st.MAX_LEN)
        replyMsg = replyMsg.decode('ascii')
        fileSize = int(replyMsg)
        bytesRead = 0
        i = 1
        while True:
            replyMsg = conn.recv(st.MAX_BUFF_SIZE)
            replyMsg = replyMsg.decode('ascii')
            print("Chunk number is: ", i)
            data = replyMsg
            print("Chunk before decryption is: ", data)
            # Decrypt the data
            data = st.decryptString(SESSION_KEY, data)
            print("Chunk after decryption is: ", data)

            i += 1
            filePtr.write(data)
            bytesRead += len(data)
            # checking whether the current chunk is the last one
            if bytesRead >= fileSize:
                print("File has been downloaded successfully..")
                filePtr.close()
                break
    except:
        print("Exception occured while downloading the file from server..")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("*** print_exception:")
        traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)
        print("*** print_tb:")
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        filePtr.close()
        return


if __name__ == '__main__':
    if len(sys.argv) != 5: 
        print ("Insufficent arguements!! Correct usage: script, client IP address, client port number, server IP address, server port number")
        exit() 

    myIP = str(sys.argv[1]) 
    myPort = int(sys.argv[2])
    serverIP = str(sys.argv[3])
    serverPort = int(sys.argv[4])
    
    # Setting private X_A
    X_A = random.randint(2, st.prime)
    
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Socket successfully created..")
        conn.bind((myIP, myPort))
        print("Socket successfully binded..")
        conn.connect((serverIP, serverPort))
    except:
        print("Creating a client connection is unsuccessful..")
        quit()
    rcvdMsg = conn.recv(st.MAX_LEN)
    if rcvdMsg:
        rcvdMsg = rcvdMsg.decode('ascii')
        print("From Server: ", rcvdMsg)
    else:
        print("No initial reply received from server..")
        quit()
    # Establishing the key between this client and server
    
    establiishKey(conn, myIP, serverIP)
    
    loginCreate(conn, myIP, serverIP)

    # authenticate(conn, myIP, serverIP)
    while True:
        print("1. Download File")
        print("2. Exit")
        try:
            choice = int(input("Enter your choice: "))
        except ValueError:
            print("Format of the input is not correct..")
            continue

        if choice == 1:
            # downloadFile(conn, myIP, myPort)
            rv = authenticate(conn, myIP, serverIP)
            if rv:
                downloadFile(conn, myIP, myPort)
            else:
                print("Username or password is incorrect..")    
        elif choice == 2:
            closeConnection(conn)
            quit()
        else:
            print("Invalid choice..")    
    # conn.close()
    