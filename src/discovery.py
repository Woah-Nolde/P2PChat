"""""!
@file broadcaster.py
@brief Hier soll der discovery server laufen
@date 21.05.2025

"""""
import time
import socket
import os
import config_manager


def ensure_singleton(port,disc_to_ui):
    """Stellt sicher, dass nur eine Instanz läuft"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(('', port))
        sock.close()
    except OSError:  
        disc_to_ui.put({"type":"singleton", "text":f"\n[Discovery] Port {port} bereits belegt - Discovery läuft bereits"})
        exit()


def discoveryloop(net_to_disc, disc_to_net,disc_to_ui,DISCOVERY_PORT):
    ensure_singleton(DISCOVERY_PORT,disc_to_ui)
    config = config_manager.load_config()
    
    #@brief Discovery Port 4000 ist eine Vorgabe
        
    DISCOVERY_PORT = config["network"]["whoisport"]
    
    """""!

    @brief im folgenden wird ein UDP socket definiert

    """""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #@brief erstelle einen internet udp socket
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #@brief erlaubt wiederverwendung von udp socket (auch belegt)
    udp_sock.bind(('', DISCOVERY_PORT)) #@brief Bindung an den Port 4000 und lauscht auf allen interfaces sei es lan , wlan oder localhost
   
    #     Da Ipv6 nicht notwendig ist, wird es nicht verwendet.
    #     udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #@brief erstelle einen internet udp socket
    #     udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #@brief erlaubt wiederverwendung von udp socket (auch belegt)
    #     udp_sock.bind(('', DISCOVERY_PORT)) #@brief Bindung an den Port 4000 und lauscht auf allen interfaces sei es lan , wlan oder localhost
    #     #print(f"[Discovery] Lausche auf UDP-Port {DISCOVERY_PORT}...")

    Bytes = 1024  #@brief maximale groeße in bytes
    clients ={}

    while True:
            data, addr = udp_sock.recvfrom(Bytes) #@brief Empfangen von Nachrichten
            message = data.decode().strip()  #@brief entfernt leerzeichen am anfang und ender der nachricht
            #print(f"[Discovery] Nachricht erhalten von {addr}: {message}")

            parts = message.split() #@brief nachricht wird decoded und aufegeteilt in hanlde command und Port (alles wird in der liste parts gespeichert)
            if not parts:  #@brief falls die nachricht leer ist,
                continue

            command = parts[0] #@brief command wird in einer variable gespeichert (sollte das erste Wort sein)

            if command == "JOIN" and len(parts) == 3: 
                handle = parts[1]                
                port = parts[2]
                ip = addr[0]
                orig_handle = handle
                # Handle-Kollision behandeln
                while handle in clients:
                    if not handle[-1].isdigit():
                        handle = f"{handle}2"
                    else:
                        num = int(handle[-1]) + 1
                        handle = f"{orig_handle}{num}"
                if handle != orig_handle:    
                    event_msg = f"HANDLE_UPDATE {handle} {port} {ip}"
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                        s.sendto(event_msg.encode(), ('255.255.255.255', 4001))

                clients[handle] = (ip, port)
                time.sleep(0.1)  # Kurze Pause, um sicherzustellen, dass der Client die Nachricht empfängt
                
                event_msg = f"USERJOIN {handle} {ip} {port}"
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    s.sendto(event_msg.encode(), ('255.255.255.255', 4001))
                
                #disc_to_ui.put({"type": "JOIN","handle": handle, "ip": ip, "port": port})
                # Rückmeldung an den Client, falls Name geändert wurde
                #if handle != orig_handle:
                 #   disc_to_ui.put({"type": "HANDLE_UPDATE", "new_handle": handle})
            elif command == "WHO":
                user_list = ", ".join( f"{h} {ip} {port}" for h, (ip, port) in clients.items() )
                #@brief bedeutet basically : Bilde für jedes Schlüssel werte paar in clients einen f-String mit der form "{h} {ip} {port}"
                #@bief die for each iteriert durch clients. Die funktion items() nimmt sich tupel raus, also Alice : (ip, port)
                response = f"KNOWUSERS {user_list}"
                udp_sock.sendto(response.encode(), addr)
                #print(f"[Discovery] Antwort gesendet an {addr}: {response}")
            elif command == "LEAVE" and len(parts) == 2: 
                handle = parts[1]
                if handle in clients:        #@brief lösche den teilnehmer aus der liste, falls er in der liste ist
                    del clients[handle]
                