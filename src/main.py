## @file main.py
# @brief Hauptmodul des P2P-Chat-Systems
# @details Koordiniert alle Komponenten (CLI, Netzwerk, Discovery) und startet die Prozesse


import socket
import threading
from config_manager import load_config, save_config, handle_autoreply
import time
from multiprocessing import Process, Queue
from discovery import discoveryloop
from messenger import network_main,send_img
import sys

def print_prompt():
    sys.stdout.write("\nCommand > ")
    sys.stdout.flush()


## @brief Gibt die eigene LAN-IP-Adresse zurück
def get_own_ip():

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Verbindung zu externem Host aufbauen (wird nicht wirklich gesendet)
            s.connect(("8.8.8.8", 80))  # Google DNS – sicher erreichbar
            return s.getsockname()[0]
    except Exception:       # @exception socket.error bei Verbindungsfehlern
        return "127.0.0.1"  # @return str IPv4-Adresse oder "127.0.0.1" bei Fehlern


## @brief Zeigt Netzwerk- und Discovery-Nachrichten an
def show_net_and_disc_messages(disc_to_ui, net_to_ui, my_handle, my_port, ui_to_net):
# @param disc_to_ui Queue für Discovery->UI
# @param net_to_ui Queue für Netzwerk->UI
# @param my_handle Eigener Nutzerhandle
# @param my_port Eigener Port
# @param ui_to_net Queue für UI->Netzwerk
    global handle  # <-- hinzufügen!
    global abwesend
    global known_users
    while True:
        if not net_to_ui.empty():
            msg = net_to_ui.get()
            if msg["type"] == "condition":
                if abwesend == True:
                    if msg["sender"] not in known_users:
                        print("\nUnbekannter Nutzer hat geschrieben. Autoreply kann nicht gesendet werden.")
                        continue
                    ip, target_port = known_users[msg["sender"]]
                    ui_to_net.put({"type": "MSG", "text": msg["text"], "target_ip": ip, "target_port": target_port, "handle":handle})
                    
                        
            
            if msg["type"] == "HANDLE_UPDATE":
                if int (msg["port"]) == my_port:
                    print(f"\n[Discovery] Dein Name ist bereits vergeben. Neuer Name: {msg['new_handle']}")
                    handle = msg["new_handle"]
                    print_prompt()
        
            if msg["type"] == "LEAVE":
                if msg["handle"] == handle:
                    continue
                print("\n[Discovery]", msg["handle"], "hat den Chat verlassen.")
                print_prompt()
            if msg["type"] == "JOIN":
  
                if msg["handle"] == handle and get_own_ip() == msg["ip"] :
                    continue
                print("\n[Discovery]", msg["handle"], "ist nun online!", msg["ip"], ":", msg["port"])
                print_prompt()
            if msg["type"] == "WHO_RESPONSE":        
                known_users = msg["users"]
                if not known_users or (len(known_users) == 1 and my_handle in known_users):
                    print("Niemand online, außer dir!")
                else:
                    print(f"\nEntdeckte Nutzer: {', '.join(known_users.keys())}")

            if msg["type"] == "recv_msg":
                sender = msg["sender"]
                text = msg["text"]
                print(f"\n[Nachricht] von {sender} {text}", end="")
                if abwesend == True:
                    print("\n[Abwesend-Modus] Du bist abwesend.\nAbwesend-Modus verlassen? klick [ENTER]: ")
                    continue
                print_prompt()
            
               
                

        if not disc_to_ui.empty():
            msg = disc_to_ui.get()
            if msg["type"] == "singleton":
                print(msg["text"])
# @details Verarbeitet:
# - Nachrichteneingang
# - Nutzer-Updates (JOIN/LEAVE)
# - Autoreply-Logik


## @brief Sendet JOIN-Broadcastnachricht
# @protocol JOIN <Handle> <Port>
def send_join(handle, port):
# @param handle Nutzerhandle
# @param port Portnummer
    msg = f"JOIN {handle} {port}"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(msg.encode(), ('255.255.255.255', 4000))

    # try:
    #       with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
    #          s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #          s.sendto(msg.encode(), ('ff02::1', 4000, 0, 0))
    # except:
    #       with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    #           s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #           s.sendto(msg.encode(), ('255.255.255.255', 4000))


## @brief Sendet LEAVE-Nachricht an alle    
# @protocol LEAVE <Handle>
def send_leave(handle, whoisport):
# @param handle Nutzerhandle
# @param whoisport Discovery-Port
    global known_users
    message = f"LEAVE {handle}"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(message.encode(), ('255.255.255.255', whoisport))
    

    for h, (ip, port) in known_users.items():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(message.encode(), (ip, port))
    # try:
    #     with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
    #         s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #         s.sendto(message.encode(), ('ff02::1', whoisport, 0, 0))
    # except:
    #     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    #         s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #         s.sendto(message.encode(), ('255.255.255.255', whoisport))


## @brief Haupt-CLI-Loop     
def cli_loop(whoisport, ui_to_net, net_to_ui, port, p1, p2):
# @param whoisport Discovery-Port
# @param ui_to_net Queue für UI->Netzwerk
# @param net_to_ui Queue für Netzwerk->UI
# @param port Eigener Port
# @param p1 Netzwerk-Prozess
# @param p2 Discovery-Prozess
    global known_users
    global handle  # <-- hinzufügen!
    global abwesend
    known_users = {}
    

    print(f"hey {handle} du bist online")
    print("Verfügbar: who, users, send, img, quit, config, name, abwesend")

    while True:
        try:
            if not abwesend:
                command = input("Command > ").strip()
            elif abwesend:
                command = "abwesend"

            if command == "abwesend":
                abwesend = True
                print("[Abwesend-Modus] Du bist jetzt abwesend.")
                ui_to_net.put({"type": "condition", "abwesend":True })
                while True:
                        input("Abwesend-Modus verlassen? klick [ENTER]: ").strip().lower()
                        abwesend = False
                        if abwesend == False:
                            break
                print("[Abwesend-Modus] Du bist wieder verfügbar.") 
                continue

            if command == "who":
                ui_to_net.put({"type": "WHO"})
                time.sleep(0.3)

            elif command == "users":
                if not known_users:
                    print("Keine bekannten Nutzer. Nutze 'who'.")
                else:
                    for h, (ip, p) in known_users.items():
                        print(f"{h} → {ip}:{p}")

            elif command.startswith("send"):
                parts = command.split(" ", 2)
                if len(parts) < 3:
                    print("Verwendung: send <handle> <nachricht>")
                    continue
                target, message = parts[1], parts[2]
                if target not in known_users:
                    print("Unbekannter Nutzer. Nutze 'who'.")
                    continue
                ip, target_port = known_users[target]
                ui_to_net.put({"type": "MSG", "text": message, "target_ip": ip, "target_port": target_port, "handle": handle})

            elif command.startswith("img"):
                parts = command.split(" ", 2)
                if len(parts) < 3:
                    print("Verwendung: img <handle> <pfad_zum_bild>")
                    continue
                target, pfad = parts[1], parts[2]
                if target not in known_users:
                    print("Unbekannter Nutzer. Nutze 'who'.")
                    continue
                ip, port = known_users[target]
                ui_to_net.put({"type": "IMG", "IP": ip, "PORT": port, "PFAD": pfad, "HANDLE": handle})
                #send_img(ip, port, pfad)
                #continue

            elif command.startswith("config"):
                from config_manager import edit_config, show_config, load_config
                
                parts = command.split()
                if len(parts) == 1:
                    # Nur 'config' eingegeben - Hilfe anzeigen
                    print("""
Config-Befehle:
  config show       - Aktuelle Konfiguration anzeigen
  config edit       - Interaktive Konfigurationsbearbeitung
  config reload     - Konfiguration neu laden
                    """)
                    
                elif parts[1] == "show":
                    # Konfiguration anzeigen
                    config = load_config()
                    print("\nAktuelle Konfiguration:")
                    for section in config:
                        print(f"[{section}]")
                        for key, value in config[section].items():
                            print(f"  {key} = {value}")
                    print()
                
                elif parts[1] == "edit":
                    # Interaktive Bearbeitung
                    old_handle = handle
                    config = edit_config()
                    handle = config["user"]["handle"]
                    
                    if old_handle != handle:
                        send_leave(old_handle, whoisport)
                        send_join(handle, port)
                        print(f"\n[Info] Handle wurde von '{old_handle}' zu '{handle}' geändert")
                    print("[Info] Konfiguration aktualisiert. ManNetzwerkänderungen benötigen Neustart.")
                
                elif parts[1] == "reload":
                    # Konfiguration neu laden
                    config = load_config()
                    handle = config["user"]["handle"]
                    print("[Info] Konfiguration neu geladen. Aktueller Handle:", handle)
                
                else:
                    print("Ungültiger config-Befehl. Verfügbar: show, edit, reload, set")
                
                continue


            elif command == "quit":
                send_leave(handle, whoisport)
                print("Tschüss!")
                time.sleep(0.5)
                p1.terminate()
                
                exit()

            elif command == "name":
                neuer_name = input("Neuer Handle: ").strip()
                send_leave(handle, whoisport)
                config = load_config()
                config["user"]["handle"] = neuer_name
                save_config(config)
                handle = neuer_name  # Laufzeit-Änderung übernehmen
                send_join(handle, port)
                print(f"Name geändert zu {neuer_name}.")
                

            else:
                print("Unbekannter Befehl. Verfügbare: who, users, send, img, quit, config, name, abwesend")

        except KeyboardInterrupt:
                   
            
             send_leave(handle, whoisport)
            
             print("\n[Client] Abbruch mit Strg+C. LEAVE gesendet.")
             p1.terminate()
             exit()
# @details Verarbeitet Befehle:
# - who: Nutzersuche
# - send: Nachricht versenden
# - img: Bild versenden
# - quit: Beenden
# - name: Handle ändern
# - abwesend: Autoreply-Modus



## @brief Findet freien UDP-Port
def find_free_port(start_port, end_port):
# @param start_port Startport
# @param end_port Endport
    for port in range(start_port, end_port + 1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', port))
            sock.close()
            return port  # @return int Freier Port
        except OSError:
            continue  # @exception OSError Wenn Port bereits belegt ist
    raise RuntimeError(f"Kein freier UDP-Port im Bereich {start_port}-{end_port} gefunden!")  # @exception RuntimeError Wenn kein Port frei ist




## @brief Hauptfunktion
# @details Startet:
# 1. Konfiguration
# 2. Netzwerk-Prozess
# 3. Discovery-Prozess
# 4. CLI-Oberfläche
def main():
    global abwesend
    abwesend = False
    global handle  # <-- hinzufügen!
    config = load_config()
    handle = config["user"]["handle"] 
    whoisport = config["network"]["whoisport"]
    port = find_free_port(config["network"]["port_range"][0], config["network"]["port_range"][1]) 
    print(f"Starte Chat mit Handle '{handle}' auf Port {port} (Discovery Port: {whoisport})")

# @section Startup-Sequenz
# @startuml
# title Startsequenz
# start
# :Lade Konfiguration;
# :Starte Netzwerkprozess;
# :Starte Discovery;
# :Starte CLI;

    ui_to_net = Queue()
    net_to_ui = Queue()
    net_to_disc = Queue()
    disc_to_net = Queue()
    disc_to_ui = Queue()
    p1 = Process(target=network_main, args=(ui_to_net, net_to_ui, net_to_disc, disc_to_net, port))
    p1.start()


    thread = threading.Thread(target=show_net_and_disc_messages, args=(disc_to_ui, net_to_ui, handle,port, ui_to_net))
    thread.daemon = True
    thread.start()


    
    p2 = Process(target=discoveryloop, args=(net_to_disc, disc_to_net, disc_to_ui, whoisport), daemon=True)
    p2.start()
    time.sleep(0.2)

    send_join(handle, port)
    cli_loop(whoisport, ui_to_net, net_to_ui, port, p1, p2)

if __name__ == "__main__":  # @note Startpunkt des Programms
    main()
