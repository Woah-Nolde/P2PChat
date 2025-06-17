import socket
import os
from config_manager import load_config, save_config, lookup_handle
from discovery import send_leave

def run_cli():
    # Lade Konfiguration beim Start
    config = load_config()
    my_handle = config['user']['handle']
    known_users = {}  # Speichert bekannte Nutzer: {handle: (ip, port)}
    
    print(f"\nChat gestartet als {my_handle}")
    print("Tippe 'help' für Befehlsliste\n")

    while True:
        try:
            # Benutzereingabe lesen
            user_input = input("> ").strip()
            
            if not user_input:
                continue
                
            # Hilfe-Befehl
            if user_input == "help":
                print("\nBefehle:")
                print("  who           - Suche nach aktiven Nutzern")
                print("  users         - Zeige bekannte Nutzer")
                print("  msg <nutzer> <nachricht> - Sende Nachricht")
                print("  img <nutzer> <pfad>     - Sende Bild")
                print("  config        - Ändere Einstellungen")
                print("  quit          - Beende den Chat\n")
                continue
                
            # WHO-Befehl: Suche nach anderen Nutzern
            if user_input == "who":
                send_who_broadcast(config['network']['whoisport'])
                print("Suche nach Nutzern...")
                continue
                
            # USERS-Befehl: Zeige bekannte Nutzer
            if user_input == "users":
                if not known_users:
                    print("Keine Nutzer bekannt. Tippe 'who' zum Suchen.")
                else:
                    print("\nBekannte Nutzer:")
                    for handle, (ip, port) in known_users.items():
                        print(f"  {handle} - {ip}:{port}")
                    print()
                continue
                
            # MSG-Befehl: Nachricht senden
            if user_input.startswith("msg "):
                parts = user_input.split(maxsplit=2)  # max 2 Splits für handle und nachricht
                if len(parts) < 3:
                    print("Fehler: msg <nutzer> <nachricht>")
                    continue
                    
                handle = parts[1]
                message = parts[2]
                
                # Suche den Nutzer in der bekannten Liste
                if handle not in known_users:
                    print(f"Nutzer {handle} nicht bekannt. Tippe 'who' zum Suchen.")
                    continue
                    
                # Sende die Nachricht
                ip, port = known_users[handle]
                send_message(handle, ip, port, message)
                print(f"Nachricht an {handle} gesendet")
                continue
                
            # IMG-Befehl: Bild senden
            if user_input.startswith("img "):
                parts = user_input.split(maxsplit=2)
                if len(parts) < 3:
                    print("Fehler: img <nutzer> <bildpfad>")
                    continue
                    
                handle = parts[1]
                image_path = parts[2]
                
                # Prüfe ob Bild existiert
                if not os.path.exists(image_path):
                    print("Fehler: Bild nicht gefunden")
                    continue
                    
                # Suche den Nutzer
                if handle not in known_users:
                    print(f"Nutzer {handle} nicht bekannt. Tippe 'who' zum Suchen.")
                    continue
                    
                # Sende das Bild
                ip, port = known_users[handle]
                send_image(handle, ip, port, image_path)
                print(f"Bild an {handle} gesendet")
                continue
                
            # CONFIG-Befehl: Einstellungen ändern
            if user_input == "config":
                new_handle = input("Neuer Nutzername: ").strip()
                if new_handle:
                    config['user']['handle'] = new_handle
                    save_config(config)
                    print("Änderungen gespeichert. Starte den Chat neu.")
                continue
                
            # QUIT-Befehl: Chat beenden
            if user_input == "quit":
                send_leave(my_handle, config['network']['whoisport'])
                print("Chat wird beendet...")
                break
                
            # Unbekannter Befehl
            print("Unbekannter Befehl. Tippe 'help' für Hilfe")
            
        except KeyboardInterrupt:
            send_leave(my_handle, config['network']['whoisport'])
            print("\nChat wird beendet...")
            break
        except Exception as e:
            print(f"Fehler: {str(e)}")

def send_who_broadcast(whoisport):
    """Sendet WHO-Broadcast um Nutzer zu finden"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b"WHO\n", ("255.255.255.255", whoisport))
        sock.close()
    except Exception as e:
        print(f"Fehler beim Senden: {str(e)}")

def send_message(handle, ip, port, message):
    """Sendet eine Textnachricht an einen Nutzer"""
    try:
        # Ersetze Leerzeichen in der Nachricht gemäß Protokoll
        safe_message = message.replace(" ", "\\ ")
        msg = f"MSG {handle} {safe_message}\n"
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(msg.encode(), (ip, port))
        sock.close()
    except Exception as e:
        print(f"Fehler beim Nachricht senden: {str(e)}")

def send_image(handle, ip, port, image_path):
    """Sendet ein Bild an einen Nutzer"""
    try:
        # Lese Bildgröße
        filesize = os.path.getsize(image_path)
        
        # Sende zuerst den IMG-Header
        header = f"IMG {handle} {filesize}\n"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(header.encode(), (ip, port))
        
        # Dann sende die Bilddaten
        with open(image_path, "rb") as f:
            data = f.read()
            sock.sendto(data, (ip, port))
            
        sock.close()
    except Exception as e:
        print(f"Fehler beim Bild senden: {str(e)}")

if __name__ == "__main__":
    run_cli()