"""
@file discovery.py
@brief Implementierung des Discovery-Servers für das SLCP-Chat-Programm
@details Dieser Dienst verwaltet die Teilnehmerliste und antwortet auf Broadcast-Anfragen.
@date 21.05.2025
"""

import time
import socket
import os
import config_manager

def ensure_singleton(port, disc_to_ui):
    """
    @brief Stellt sicher, dass nur eine Instanz des Discovery-Dienstes läuft
    @param port Der Port, auf dem der Dienst laufen soll
    @param disc_to_ui IPC-Queue für Nachrichten an die Benutzeroberfläche
    @details Versucht, den angegebenen Port zu binden. Falls dies fehlschlägt, 
             wird angenommen, dass bereits eine Instanz läuft und das Programm beendet.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(('', port))
        sock.close()
    except OSError:  
        disc_to_ui.put({"type":"singleton", "text":f"\n[Discovery] Port {port} bereits belegt - Discovery läuft bereits"})
        exit()

def discoveryloop(net_to_disc, disc_to_net, disc_to_ui, DISCOVERY_PORT):
    """
    @brief Hauptfunktion des Discovery-Dienstes
    @param net_to_disc IPC-Queue für Nachrichten vom Netzwerkmodul
    @param disc_to_net IPC-Queue für Nachrichten an das Netzwerkmodul
    @param disc_to_ui IPC-Queue für Nachrichten an die Benutzeroberfläche
    @param DISCOVERY_PORT Port für den Discovery-Dienst
    @details Diese Funktion implementiert den Hauptloop des Discovery-Servers:
             - Verwaltet die Liste aktiver Teilnehmer
             - Verarbeitet JOIN/LEAVE/WHO Nachrichten
             - Sendet Antworten auf WHO-Anfragen
    """
    ensure_singleton(DISCOVERY_PORT, disc_to_ui)
    config = config_manager.load_config()
    
    # Discovery Port 4000 ist eine Vorgabe laut Protokollspezifikation
    DISCOVERY_PORT = config["network"]["whoisport"]
    
    # UDP Socket Konfiguration
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.bind(('', DISCOVERY_PORT))
    
    # Technische Notiz: IPv6 wird bewusst nicht unterstützt, da nicht in den Anforderungen gefordert
    # und die Protokollspezifikation IPv4-Adressen in den Beispielen zeigt
    
    MAX_MESSAGE_SIZE = 1024  # Maximale Nachrichtengröße in Bytes (laut Protokoll 512 Zeichen + Puffer)
    clients = {}  # Dictionary zur Speicherung aktiver Teilnehmer {Handle: (IP, Port)}

    while True:
        # Nachrichtenempfang
        data, addr = udp_sock.recvfrom(MAX_MESSAGE_SIZE)
        message = data.decode().strip()
        
        # Nachrichtenverarbeitung
        parts = message.split()
        if not parts:  # Leere Nachrichten ignorieren
            continue

        command = parts[0]  # Erstes Wort ist der Befehl

        # JOIN-Befehl verarbeiten (Protokoll: JOIN <Handle> <Port>)
        if command == "JOIN" and len(parts) == 3: 
            handle = parts[1]                
            port = parts[2]
            ip = addr[0]
            orig_handle = handle
            
            # Handle-Kollision behandeln (eindeutige Handles erzwingen)
            """@brief Behandelt Handle-Kollisionen durch automatische Nummerierung
            @details Falls der Handle existiert, wird eine Ziffer angehängt (z. B. Alice → Alice2).
            Bei weiteren Kollisionen wird die Ziffer inkrementiert.
            @note Nicht thread-safe! Falls parallele JOINs, könnte dieselbe Nummer vergeben werden.
            """
            while handle in clients:             
                if not handle[-1].isdigit():
                    handle = f"{handle}2"
                else:
                    num = int(handle[-1]) + 1
                    handle = f"{orig_handle}{num}"
            
            # Benachrichtigung über Handle-Änderung senden
            if handle != orig_handle:    
                event_msg = f"HANDLE_UPDATE {handle} {port} {ip}"
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    s.sendto(event_msg.encode(), ('255.255.255.255', 4001))

            # Neuen Teilnehmer zur Liste hinzufügen
            clients[handle] = (ip, port)
            time.sleep(0.5)  # Kurze Pause für zuverlässige Verarbeitung. Sonst könnte die UI den Hadnle update zu spät erhalten
            
            # Benachrichtigung über neuen Teilnehmer senden
            event_msg = f"USERJOIN {handle} {ip} {port}"
            #disc_to_net.put({"type":"JOIN", "handle":handle, "ip":ip, "port":port}) Da wir das Broadcasten nutzen und diese als verlässlicher sehen, ist das nicht mehr nötig.
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.sendto(event_msg.encode(), ('255.255.255.255', 4001))
        
        # WHO-Befehl verarbeiten (Protokoll: WHO)
        elif command == "WHO":
            # Liste aller bekannten Teilnehmer erstellen
            user_list = ", ".join(f"{h} {ip} {port}" for h, (ip, port) in clients.items())
            response = f"KNOWUSERS {user_list}"
            udp_sock.sendto(response.encode(), addr)
        
        # LEAVE-Befehl verarbeiten (Protokoll: LEAVE <Handle>)
        elif command == "LEAVE" and len(parts) == 2: 
            handle = parts[1]
            if handle in clients:
                del clients[handle]
                