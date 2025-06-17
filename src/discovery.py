"""""!
@file broadcaster.py
@brief Hier soll der discovery server laufen
@date 21.05.2025

"""""

import socket
import os
import config_manager

def send_join(handle, port, whoisport):
    msg = f"JOIN {handle} {port}" 
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #@brief stelle auf socket Ebene ein, dass an die Broadcast Adresse versendet werden kann
        s.sendto(msg.encode(), ('255.255.255.255', whoisport)) #@brief schicke JOIN Nachricht an Broadcast Adresse

def send_leave(handle, whoisport):
    message = f"LEAVE {handle}"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(message.encode(), ('255.255.255.255', whoisport))
    
def discover_users(whoisport):
     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', 0))
        s.settimeout(0.1)
        s.sendto("WHO".encode(), ('255.255.255.255', whoisport))
        try:
            data, addr = s.recvfrom(1024)
            print(f"[Client] Antwort: {data.decode()}")
            return data.decode()
        except socket.timeout:
            print("[Client] Keine Antwort erhalten.")
            return ""





def discoveryloop():
    config = config_manager.load_config()
    
    #@brief Discovery Port 4000 ist eine vorgaben
        
    DISCOVERY_PORT = config["network"]["whoisport"]
    
    """""!

    @brief im folgenden wird ein UDP socket definiert

    """""
    
   
   
    try:
        udp_sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)  
        udp_sock.bind(('', DISCOVERY_PORT))
        print(f"[Discovery] Lausche auf UDP-Port {DISCOVERY_PORT}...")
    except OSError:
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #@brief erstelle einen internet udp socket
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #@brief erlaubt wiederverwendung von udp socket (auch belegt)
        udp_sock.bind(('', DISCOVERY_PORT)) #@brief Bindung an den Port 4000 und lauscht auf allen interfaces sei es lan , wlan oder localhost
        print(f"[Discovery] Lausche auf UDP-Port {DISCOVERY_PORT}...")
    Bytes = 1024  #@brief maximale groeße in bytes
    clients ={}

    while True:
            data, addr = udp_sock.recvfrom(Bytes) #@brief Empfangen von Nachrichten
            message = data.decode().strip()  #@brief entfernt leerzeichen am anfang und ender der nachricht
            print(f"[Discovery] Nachricht erhalten von {addr}: {message}")

            parts = message.split() #@brief nachricht wird decoded und aufegeteilt in hanlde command und Port (alles wird in der liste parts gespeichert)
            if not parts:  #@brief falls die nachricht leer ist,
                continue

            command = parts[0] #@brief command wird in einer variable gespeichert (sollte das erste Wort sein)

            if command == "JOIN" and len(parts) == 3: 
                handle = parts[1]                
                port = parts[2]
                ip = addr[0]              #@brief einzelnen teile der liste 'parts' werden gespeichert

                clients[handle] = (ip, port) #@brief speicher die Sender informationen in 'clients'
                print(f"[Discovery] {handle} ist online: {ip}:{port}")
            elif command == "WHO":
                user_list = ", ".join( f"{h} {ip} {port}" for h, (ip, port) in clients.items() )
                #@brief bedeutet basically : Bilde für jedes Schlüssel werte paar in clients einen f-String mit der form "{h} {ip} {port}"
                #@bief die for each iteriert durch clients. Die funktion items() nimmt sich tupel raus, also Alice : (ip, port)
                response = f"KNOWUSERS {user_list}"
                udp_sock.sendto(response.encode(), addr)
                print(f"[Discovery] Antwort gesendet an {addr}: {response}")
            elif command == "LEAVE" and len(parts) == 2: 
                handle = parts[1]
                if handle in clients:        #@brief lösche den teilnehmer aus der liste, falls er in der liste ist
                    del clients[handle]
                print(f"[Discovery] {handle} hat den Chat verlassen.")
    















        

