import config #toml
import socket
from config_manager import load_config, save_config, lookup_handle
from discovery import send_leave
def run_cli():
    config= load_config()
    known_users = {}
    print("Verfügbare Befehle: who, users, msg, img, name, quit")


    while True:
        try:
            command = input("Command > ").strip()

            if command == "who":
                send_who()

            elif command == "users":
                print("Bekannte Benutzer:")
                for user, (ip, port) in known_users.items():
                    print   (f"{user} - {ip}:{port}")

            elif command.startswith("msg"):
                parts = command.split()
                if len(parts) >= 3:
                    handle= parts[1]
                    message = " ".join(parts[2:])
                    send_msg(handle, message)
                else:
                    print("Benutzung: msg <handle> <message>")

            elif command.startswith("img:"):
                parts   = command.split()
                if  len(parts) == 3:
                    send_img(parts[1], parts[2])
                else:
                    print("Benutzung: img:<handle> <image_path>")

            elif command == "name":
                neuer_name = input("Neuer Handle: ").strip()
                config['handle'] = neuer_name
                save_config(config)
                print("Name geändert, bitte neu starten.")
            
            elif command == "quit":
                send_leave()
                print("Chat wird beendet...")
                break

            
            else:
                print("Unbekannter Befehl. Verfügbare Befehle: who, users, msg, img, name, quit")

        except KeyboardInterrupt:
            send_leave()
            print("\n[Client] Abbruch mit Strg+C. LEAVE gesendet.")
            break

def send_who():
    config = load_config()
    msg = "WHO\n"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(msg.encode('utf-8'), ("255.255.255.255", config["whosiport"]))

def send_msg(handle, text):
    peer = lookup_handle(handle)
    if peer:
        ip, port = peer
        msg = f"MSG {handle} {text}\n"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(msg.encode(), (ip, port))
    else:
        print("Empfänger nicht gefunden.")

def send_img(handle, filepath):
    peer = lookup_handle(handle)
    if not peer:
        print("Empfänger nicht gefunden.")
        return
    try:
        with open(filepath, "rb") as img_file:
            data = img_file.read()
        ip, port = peer
        header = f"IMG {handle} {len(data)}\n".encode()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(header, (ip, port))
            sock.sendto(data, (ip, port))
        print(f"Bild an {handle} gesendet.")
    except FileNotFoundError:
        print("Bilddatei nicht gefunden.")