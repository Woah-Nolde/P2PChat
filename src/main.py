import socket
import threading
from network.messenger import send_msg
from network.messenger import receive_messages

def send_join(handle, port):
    msg = f"JOIN {handle} {port}" 
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #@brief stelle auf socket Ebene ein, dass an die Broadcast Adresse versendet werden kann
        s.sendto(msg.encode(), ('255.255.255.255', 4000)) #@brief schicke JOIN Nachricht an Broadcast Adresse

send_msg()
receive_messages()


def main():
    handle = input("Benutzernamen: ") 
    port = int(input("Port: "))     #@brief Port auf dem man erreichbar ist
    send_join(handle,port)
    thread = threading.Thread(target=receive_messages, args=(port,))
    thread.daemon = True
    thread.start()


    
    

if __name__ == "__main__":
    main()