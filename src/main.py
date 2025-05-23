import socket
import threading

def send_join(handle, port):
    msg = f"JOIN {handle} {port}" 
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #@brief stelle auf socket Ebene ein, dass an die Broadcast Adresse versendet werden kann
        s.sendto(msg.encode(), ('255.255.255.255', 4000)) #@brief schicke JOIN Nachricht an Broadcast Adresse


        