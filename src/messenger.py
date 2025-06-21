# messenger.py
import socket
import os
import threading
import time
import config_manager

# NEU: SLCP-Protokoll-Parser
def parse_slcp(message):
    if message.startswith("MSG"):
        parts = message[4:].split(" ", 1)
        if len(parts) == 2:
            sender = parts[0]
            text = parts[1].replace("%20", " ")  # Maskierung auflösen
            return ("MSG", sender, text)
    return ("UNKNOWN", None, message)



def network_main(ui_to_net, net_to_ui, net_to_disc, disc_to_net,port):
    global abwesend
    

    thread = threading.Thread(target=receive_messages, args=(port,net_to_ui))
    thread.daemon = True
    thread.start()
    threading.Thread(target=discovery_listener, args=(net_to_ui, port), daemon=True).start()
    while True:
        if not disc_to_net.empty():
            msg = disc_to_net.get() # noch keine ahnung warum ich das emmpfange. habe was geändert.
        if not ui_to_net.empty():
            msg = ui_to_net.get()  # Holt die Nachricht aus der Queue
            if msg["type"] == "condition":
                if msg["abwesend"] == True:
                    abwesend = True
                    
            if msg["type"] == "IMG":
                send_img(msg["IP"], msg["PORT"], msg["PFAD"], msg.get("HANDLE"))
        
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
    # Das Bild wird als Binärdatei gespeichert (z.B. empfangen_Alice_1718031234.bin).
    # Texteditoren können Binärdateien nicht anzeigen, daher kommt die Meldung.
    # Um das Bild zu sehen, öffne die Datei mit einem Bildbetrachter oder benenne sie ggf. in .jpg/.png um,
    # falls du weißt, welches Format gesendet wurde.
def receive_messages(my_port, net_to_ui):
    config = config_manager.load_config()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', my_port))
    except OSError:
        print(f"[Fehler] Port {my_port} ist bereits belegt. Bitte einen anderen Port wählen.")
        return

    expected_img = None  # (handle, size)
    img_data = b""
    img_filename = ""
    global abwesend  #@brief falls der Nutzer abwesend ist, wird die Nachricht nicht weitergeleitet
    abwesend = False  #@brief Variable, die angibt, ob der Nutzer abwesend ist

    while True:
        data, addr = sock.recvfrom(512)
        try:
            text = data.decode()
            typ2, sender2, text2 = parse_slcp(data.decode(errors="ignore"))
            if abwesend and typ2 == "MSG":  #@brief falls der Nutzer abwesend ist, wird die Nachricht nicht weitergeleitet
               typ2, sender2, text2 = parse_slcp(data.decode(errors="ignore"))
               
               text2 = config["user"]["autoreply"] #@brief falls der Nutzer abwesend ist, wird die Autoreply-Nachricht gesendet
               net_to_ui.put({"type": "condition", "sender": sender2, "text": text2}) #@brief leitet die Nachricht an die UI weiter
               # ich nutze hier sender2 und text2, weil ich die Variablen nicht umbenennen möchte, da sie schon in der Funktion definiert sind.
            
            
               
               

            message = data.decode().strip()
            parts = message.split()
            if not parts:  #@brief falls die nachricht leer ist,
                continue
            command = parts[0] 
            if command == "LEAVE" and len(parts) == 2:
                net_to_ui.put({"type": "LEAVE", "handle": parts[1]})
            if text.startswith("IMG "):
                # Header empfangen
                parts = text.split()
                if len(parts) == 3:
                    handle, size = parts[1], int(parts[2])
                    expected_img = (handle, size)
                    img_data = b""
                    img_filename = f"empfangen_{handle}_{int(time.time())}.jpg"
                    continue
            # Sonstige Textnachrichten
        except UnicodeDecodeError:
            # Binärdaten empfangen
            if expected_img:
                img_data += data
                if len(img_data) >= expected_img[1]:
                    image_dir = os.path.join("src", "image")
                    os.makedirs(image_dir, exist_ok=True)  # Ordner erstellen, falls nicht vorhanden
                    img_filename = os.path.join(image_dir, f"empfangen_{handle}_{int(time.time())}.jpg")
                    
                    with open(img_filename, "wb") as f:
                        f.write(img_data[:expected_img[1]])
                    print(f"[Empfänger] Bild empfangen von {addr} → gespeichert als {img_filename}")
                    expected_img = None
                    img_data = b""
            continue

        # ...vorheriger Code für normale Nachrichten...
        typ, sender, text = parse_slcp(data.decode(errors="ignore"))
        if typ == "MSG":
            net_to_ui.put({"type": "recv_msg", "sender": sender, "text": text})
        else:
            print(f"\n[Unbekanntes Format] {data.decode(errors='ignore')}\n> ", end="")


def discovery_listener(net_to_ui, my_port):
    """
    Lauscht auf Discovery-Broadcast-Nachrichten (z.B. USERJOIN, USERLEAVE) und leitet sie per IPC weiter.
    """
    DISCOVERY_EVENT_PORT = 4001 # Zusätzlich zu Port 4000 (JOIN/WHO/LEAVE)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', DISCOVERY_EVENT_PORT))
    dataold = None

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode().strip()


          
        if message == dataold:
            continue # Wenn die Daten gleich geblieben sind, überspringen damit keine Dopplungen entstehen
        # Speichern der alten Nachricht, um Dopplungen zu vermeiden  
        dataold = message    

        if not message:
            continue

        parts = message.split()
        if len(parts) < 2:
            continue

        cmd = parts[0]

        # Beispiel: USERJOIN Alice 192.168.1.42 5000
        if cmd == "USERJOIN" and len(parts) == 4:
            handle, ip, port = parts[1], parts[2], parts[3]
            net_to_ui.put({"type": "JOIN", "handle": handle, "ip": ip, "port": port})

        elif cmd == "USERLEAVE" and len(parts) == 2:
            handle = parts[1]
            net_to_ui.put({"type": "LEAVE", "handle": handle})

        elif cmd == "HANDLE_UPDATE" and len(parts) == 4:
            new_handle = parts[1]
            port = parts[2]
            ip = parts[3]
            net_to_ui.put({"type": "HANDLE_UPDATE", "new_handle": new_handle, "port": port, "ip":ip})

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


def send_msg(target_ip, target_port, target_handle, text):
    text_masked = text.replace(" ", "%20")
    msg = f"MSG {target_handle} {text_masked}"
    if len(msg) > 512:
        raise ValueError("Nachricht zu lang, maximal 512 Zeichen erlaubt.") # Maximale Länge von Nachrichten
    if ":" in target_ip:
        with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
            s.sendto(msg.encode(), (target_ip, target_port, 0, 0))
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(msg.encode(), (target_ip, target_port))


def send_img(target_ip, target_port, filename, handle=None):
    if not os.path.exists(filename):
        print(f"[Fehler] Bilddatei {filename} nicht gefunden.")
        return

    with open(filename, "rb") as f:
        image_data = f.read()

    size = len(image_data)
    # 1. Header senden
    header = f"IMG {handle if handle else 'unknown'} {size}".encode()
    if ":" in target_ip:
        with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
            s.sendto(header, (target_ip, target_port, 0, 0))
            for i in range(0, size, 512):
                s.sendto(image_data[i:i+512], (target_ip, target_port, 0, 0))
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(header, (target_ip, target_port))
            for i in range(0, size, 512):
                s.sendto(image_data[i:i+512], (target_ip, target_port))
    print(f"[Sender] Bild {filename} an {target_ip}:{target_port} gesendet.")
