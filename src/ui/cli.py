import config #toml
import socket
from config_manager import load_config, save_config, edit_config, lookup_handle
from discovery import send_leave

# @brief Startet die Kommandozeilen-Oberfläche (CLI) für den Chat.
# Die CLI unterstützt Befehle zum Versenden von Textnachrichten, Bildern,
# zur Abfrage von Teilnehmern und zur Änderung der Konfiguration.
# Lädt Konfiguration, zeigt Benutzerbefehle und verarbeitet Eingaben.
def run_cli():
    config= load_config() # Konfiguration aus Datei laden
    known_users = {}
    print(f"Hallo, {config['user']['handle']}!")  # Benutzername anzeigen und Begrüßung
    print("Verfügbare Befehle: who, users, msg, img, name, quit") 


    while True:
        try:
            command = input("Command > ").strip() # Befehl eingeben

            if command == "who":
                send_who() # WHO-Befehl senden

            elif command == "users":
                print("Bekannte Benutzer:")
                for user, (ip, port) in known_users.items(): # Bekannte Nutzer angeben
                    print   (f"{user} - {ip}:{port}")

            elif command.startswith("msg"):
                parts = command.split()
                if len(parts) >= 3:
                    handle= parts[1]
                    message = " ".join(parts[2:])
                    send_msg(handle, message) # Nachricht senden
                else:
                    print("Benutzung: msg <handle> <message>")

            elif command.startswith("img:"):
                parts   = command.split()
                if  len(parts) == 3:
                    send_img(parts[1], parts[2]) # Bild senden
                else:
                    print("Benutzung: img:<handle> <image_path>")

            elif command == "name":
                neuer_name = input("Neuer Handle: ").strip() # Name ändern
                config['handle'] = neuer_name
                save_config(config) # Veränderung speichern
                print("Name geändert, bitte neu starten.")
            
            elif command == "config":
               edit_config() # Konfiguration ändern
            
            elif command == "quit":
                send_leave() # LEAVE senden
                print("Chat wird beendet...")
                break

            else:
                print("Unbekannter Befehl. Verfügbare Befehle: who, users, msg, img, name, quit")

        except KeyboardInterrupt:
            send_leave() # LEAVE bei strg+c
            print("\n[Client] Abbruch mit Strg+C. LEAVE gesendet.")
            break

# @brief Sendet eine WHO-Broadcast-Nachricht zur Teilnehmererkennung.
# über UDP-Broadcast gemäß dem SLCP-Protokoll.
# Diese Nachricht fragt nach allen aktiven Teilnehmern im lokalen Netz.
def send_who():
    config = load_config() # Konfiguration laden
    msg = "WHO\n"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # Broadcast aktivieren
        sock.sendto(msg.encode('utf-8'), ("255.255.255.255", config["whosiport"])) # WHO senden

# @brief Sendet eine MSG-Nachricht an den Empfänger.
# @param handle Empfänger-Handle
# @param text Nachrichtentext
# Die Nachricht wird im SLCP-Format per UDP direkt an den Empfänger verschickt.
# @param handle Handle (Benutzername) des Empfängers
# @param text Text der zu sendenden Nachricht
def send_msg(handle, text):
    peer = lookup_handle(handle) # IP und Port vom Empfänger suchen
    if peer:
        ip, port = peer
        msg = f"MSG {handle} {text}\n" # Nachricht im SLCP-Format
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(msg.encode(), (ip, port)) # Nachricht senden
    else:
        print("Empfänger nicht gefunden.")


# @brief Sendet ein Bild an Empfänger.
# @param handle Empfänger-Handle
# @param filepath Pfad zum Bild
# Die Funktion sendet zunächst einen IMG-Header mit der Dateigröße,
# anschließend die Bilddaten als UDP-Nachricht gemäß dem SLCP-Protokoll.
# @param handle Handle des Empfängers
# @param filepath Pfad zum Bild, die gesendet werden soll
def send_img(handle, filepath):
    peer = lookup_handle(handle) # Empfängeradresse suchen
    if not peer:
        print("Empfänger nicht gefunden.")
        return
    try:
        with open(filepath, "rb") as img_file:
            data = img_file.read() # Bilddatei suchen
        ip, port = peer
        header = f"IMG {handle} {len(data)}\n".encode() # Header vorbereiten
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(header, (ip, port)) # Header senden
            sock.sendto(data, (ip, port)) # Bilddaten senden
        print(f"Bild an {handle} gesendet.")
    except FileNotFoundError:
        print("Bilddatei nicht gefunden.")