
# messenger.py
import socket
import os
import threading
import time

# NEU: SLCP-Protokoll-Parser
def parse_slcp(message):
    if message.startswith("MSG:"):
        parts = message[4:].split(" ", 1)
        if len(parts) == 2:
            sender = parts[0]
            text = parts[1].replace("%20", " ")  # Maskierung auflösen
            return ("MSG", sender, text)
    return ("UNKNOWN", None, message)



def network_main(ui_to_net, net_to_ui, net_to_disc, disc_to_net,port):
    

    thread = threading.Thread(target=receive_messages, args=(port,net_to_ui))
    thread.daemon = True
    thread.start()
    threading.Thread(target=discovery_listener, args=(net_to_ui, port), daemon=True).start()
    while True:
        if not disc_to_net.empty():
            msg = disc_to_net.get()
        if not ui_to_net.empty():
            msg = ui_to_net.get()  # Holt die Nachricht aus der Queue
            if msg["type"] == "IMG":
                send_img(msg["IP"],msg["PORT"],msg["PFAD"] )
        
            if msg["type"] == "MSG":
                send_msg(msg["target_ip"],msg["target_port"] ,msg["handle"],msg["text"],)
            
            if msg["type"] == "WHO":
                response = discover_users()
                net_to_ui.put({"type":"WHO_RESPONSE","users": response})

def discover_users():
    responses = set()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', 0))
        s.settimeout(0.1)
        s.sendto("WHO".encode(), ('255.255.255.255', 4000))

        start_time = time.time()
        while time.time() - start_time < 1.0:  # Sammelphase
            try:
                data, _ = s.recvfrom(1024)
                responses.add(data.decode())  # Deduplizierung
            except socket.timeout:
                break
    
    # Alle Antworten mergen
    merged_users = {}
    for response in responses:
        users = parse_knownusers(response)
        merged_users.update(users)
    
    return merged_users

        # try:
        #     data, addr = s.recvfrom(1024)
        #     #print(f"[Client] Antwort: {data.decode()}")
        #     return data.decode()
        # except socket.timeout:
        #     print("[Client] Keine Antwort erhalten.")
        #     return ""


def parse_knownusers(response):
    if not response.startswith("KNOWUSERS "):  #@brief stellt sicher, dass es sich um die WHO anfrage handelt
        return {}

    user_info = response[len("KNOWUSERS "):] #@brief KNOWUSERS wird raus geschnitten

    users = user_info.split(", ") #@brief alles wird in die liste users gepackt und mit , getrennt (users_info ist ein großer string und jz in einer liste)
    known = {}

    for user in users:
        try:
            handle, ip, port = user.strip().split() #@brief strip entfernt leerzeichen an anfang und ende und split teilt auf in handle, ip und port
            known[handle] = (ip, int(port)) #@brief alles wird in die liste 'known' gepackt
        except ValueError:
            continue     #@brief falls das Format fehlerhaft ist

    return known

def receive_messages(my_port,net_to_ui):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', my_port))
    except OSError:
        print(f"[Fehler] Port {my_port} ist bereits belegt. Bitte einen anderen Port wählen.")
        return

    # try:
    #     sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    #     sock.bind(('::', my_port))
    #     #print(f"[Empfänger] Lausche auf Port {my_port} (IPv6) für eingehende Nachrichten...")
    # except:
    #     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     sock.bind(('', my_port))
    #     #print(f"[Empfänger] Lausche auf Port {my_port} (IPv4) für eingehende Nachrichten...")

    while True:
        data, addr = sock.recvfrom(65507)

        if data.startswith(b"IMG:"):
            parts = data.split(b":", 3)

            if len(parts) != 4:
                print(f"[Fehler] Ungültiges Bildformat von {addr}")
                continue

            filename = os.path.basename(parts[1].decode())

            try:
                size = int(parts[2].decode())
            except ValueError:
                print(f"[Fehler] Ungültiger Size-Header bei empfangener IMG-Nachricht.")
                continue

            image_data = parts[3]

            if len(image_data) != size:
                print(f"[Fehler] Bild unvollständig: erwartet {size} Bytes, empfangen {len(image_data)} Bytes.")
                continue  #  unvollständiges Bild nicht speichern

            with open("empfangen_" + filename, "wb") as f:
                f.write(image_data)

            print(f"[Empfänger] Bild empfangen von {addr} → gespeichert als empfangen_{filename}")

        else:
            message = data.decode()
            typ, sender, text = parse_slcp(message)  # NEU: Parser verwenden
            if typ == "MSG":
                #print(f"\n[Nachricht von {sender}] {text}\n> ", end="")
                net_to_ui.put({"type":"recv_msg","sender":sender,"text":text})
            else:
                print(f"\n[Unbekanntes Format] {message}\n> ", end="")


def discovery_listener(net_to_ui, my_port):
    """
    Lauscht auf Discovery-Broadcast-Nachrichten (z.B. USERJOIN, USERLEAVE) und leitet sie per IPC weiter.
    """
    DISCOVERY_EVENT_PORT = 4001 # Zusätzlich zu Port 4000 (JOIN/WHO/LEAVE)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', DISCOVERY_EVENT_PORT))

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode().strip()

        if not message:
            continue

        parts = message.split()
        if len(parts) < 2:
            continue

        cmd = parts[0]

        # Beispiel: USERJOIN Alice 192.168.1.42 5000
        if cmd == "USERJOIN" and len(parts) == 4:
            handle, ip, port = parts[1], parts[2], parts[3]
            if int(port) != my_port:  # Nur anzeigen, wenn es nicht die eigene Instanz ist
                net_to_ui.put({"type": "JOIN", "handle": handle, "ip": ip, "port": port})

        elif cmd == "USERLEAVE" and len(parts) == 2:
            handle = parts[1]
            net_to_ui.put({"type": "LEAVE", "handle": handle})

        elif cmd == "HANDLE_UPDATE" and len(parts) == 3:
            new_handle = parts[1]
            port = parts[2]
            net_to_ui.put({"type": "HANDLE_UPDATE", "new_handle": new_handle, "port": port})

        elif cmd == "KNOWUSERS":
            # Beispiel: KNOWUSERS Alice 192.168.1.2 5000, Bob 192.168.1.3 5001
            known = {}
            users_info = message[len("KNOWUSERS "):].split(", ")
            for user in users_info:
                try:
                    h, ip, p = user.strip().split()
                    known[h] = (ip, int(p))
                except ValueError:
                    continue
            net_to_ui.put({"type": "WHO_RESPONSE", "users": known})


def send_msg(target_ip, target_port, sender_handle, text):
    text_masked = text.replace(" ", "%20")
    msg = f"MSG:{sender_handle} {text_masked}"
    if ":" in target_ip:
        with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
            s.sendto(msg.encode(), (target_ip, target_port, 0, 0))
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(msg.encode(), (target_ip, target_port))


def send_img(target_ip, target_port, filename):

    if not os.path.exists(filename):
        print(f"[Fehler] Bilddatei {filename} nicht gefunden.")
        return
    
    with open(filename, "rb") as f:
        image_data = f.read()

    size = len(image_data)
    message = f"IMG:{filename}:{size}:".encode() + image_data

    if len(message) > 65507:
        print("[Fehler] Bild zu groß für ein UDP-Paket.")
        return

    if ":" in target_ip:
        with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
            s.sendto(message, (target_ip, target_port, 0, 0))
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(message, (target_ip, target_port))
    print(f"[Sender] Bild {filename} an {target_ip}:{target_port} gesendet.")
