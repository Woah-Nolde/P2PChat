import socket
import threading
from config_manager import load_config, save_config
import time
from multiprocessing import Process, Queue
from discovery import discoveryloop
from messenger import network_main,send_img
import sys

def print_prompt():
    sys.stdout.write("\nCommand > ")
    sys.stdout.flush()

def show_net_and_disc_messages(disc_to_ui, net_to_ui, my_handle, my_port):
    global handle  # <-- hinzufügen!
    while True:
        if not net_to_ui.empty():
            msg = net_to_ui.get()
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
                if msg["handle"] == handle:
                    continue
                print("\n[Discovery]", msg["handle"], "ist nun online!", msg["ip"], ":", msg["port"])
                print_prompt()
            if msg["type"] == "WHO_RESPONSE":
                global known_users
                known_users = msg["users"]
                if not known_users or (len(known_users) == 1 and my_handle in known_users):
                    print("Niemand online, außer dir!")
                else:
                    print(f"\nEntdeckte Nutzer: {', '.join(known_users.keys())}")

            if msg["type"] == "recv_msg":
                print("\n[Nachricht] von", msg["sender"], msg["text"], end="")
                print_prompt()
               
                

        if not disc_to_ui.empty():
            msg = disc_to_ui.get()
            if msg["type"] == "singleton":
                print(msg["text"])

def send_join(handle, port):
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

def send_leave(handle, whoisport):
    message = f"LEAVE {handle}"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(message.encode(), ('255.255.255.255', whoisport))
    # try:
    #     with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
    #         s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #         s.sendto(message.encode(), ('ff02::1', whoisport, 0, 0))
    # except:
    #     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    #         s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #         s.sendto(message.encode(), ('255.255.255.255', whoisport))

def cli_loop(whoisport, ui_to_net, net_to_ui, port, p1, p2):
    global known_users
    global handle  # <-- hinzufügen!
    known_users = {}
    print(f"hey {handle} du bist online")
    print("Verfügbar: who, users, send, img, quit, name")

    while True:
        try:
            command = input("Command > ").strip()

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
                print("Unbekannter Befehl. Verfügbare: who, users, send, quit, name")

        except KeyboardInterrupt:
                   
            
             send_leave(handle, whoisport)
            
             print("\n[Client] Abbruch mit Strg+C. LEAVE gesendet.")
             p1.terminate()
             exit()

def find_free_port(start_port, end_port):
    """Findet einen freien UDP-Port im angegebenen Bereich."""
    for port in range(start_port, end_port + 1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', port))
            sock.close()
            return port  # Port ist frei
        except OSError:
            continue  # Port ist belegt, nächster Versuch
    raise RuntimeError(f"Kein freier UDP-Port im Bereich {start_port}-{end_port} gefunden!")

def main():
    global handle  # <-- hinzufügen!
    config = load_config()
    handle = config["user"]["handle"]
    whoisport = config["network"]["whoisport"]
    port = find_free_port(config["network"]["port_range"][0], config["network"]["port_range"][1])
    print(f"Starte Chat mit Handle '{handle}' auf Port {port} (Discovery Port: {whoisport})")

    ui_to_net = Queue()
    net_to_ui = Queue()
    net_to_disc = Queue()
    disc_to_net = Queue()
    disc_to_ui = Queue()
    p1 = Process(target=network_main, args=(ui_to_net, net_to_ui, net_to_disc, disc_to_net, port))
    p1.start()


    thread = threading.Thread(target=show_net_and_disc_messages, args=(disc_to_ui, net_to_ui, handle,port))
    thread.daemon = True
    thread.start()


    
    p2 = Process(target=discoveryloop, args=(net_to_disc, disc_to_net, disc_to_ui, whoisport), daemon=True)
    p2.start()
    time.sleep(0.2)

    send_join(handle, port)
    cli_loop(whoisport, ui_to_net, net_to_ui, port, p1, p2)

if __name__ == "__main__":
    main()
