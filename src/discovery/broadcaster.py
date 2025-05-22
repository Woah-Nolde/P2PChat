"""""!
@file broadcaster.py
@brief Hier soll der discovery server laufen
@date 21.05.2025

"""""
import socket

#@brief Discovery Port 400 ist eine vorgaben
DISCOVERY_PORT = 4000

Bytes = 1024  #@brief maximale groeße in bytes
"""""!

@brief im folgenden wird ein UDP socket definiert

"""""
clients = {} 
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #@brief erstelle einen internet udp socket
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #@brief erlaubt wiederverwendung von udp socket (auch belegt)
udp_sock.bind(('', DISCOVERY_PORT)) #@brief Bindung an den Port 4000 und lauscht auf allen interfaces sei es lan , wlan oder localhost
print(f"[Discovery] Lausche auf UDP-Port {DISCOVERY_PORT}...") 