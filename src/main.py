import socket
import threading
from network.messenger import send_msg
from network.messenger import receive_messages

def send_join(handle, port):
    msg = f"JOIN {handle} {port}" 
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #@brief stelle auf socket Ebene ein, dass an die Broadcast Adresse versendet werden kann
        s.sendto(msg.encode(), ('255.255.255.255', 4000)) #@brief schicke JOIN Nachricht an Broadcast Adresse

def send_leave(handle):
    return



def parse_knownusers(response):
    return ""


def discover_users():
     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', 0))
        s.settimeout(2)
        s.sendto("WHO".encode(), ('255.255.255.255', 4000))
        try:
            data, addr = s.recvfrom(1024)
            print(f"[Client] Antwort: {data.decode()}")
            return data.decode()
        except socket.timeout:
            print("[Client] Keine Antwort erhalten.")
            return ""



def main():
    handle = input("Benutzernamen: ") 
    port = int(input("Port: "))     #@brief Port auf dem man erreichbar ist
    send_join(handle,port)
    thread = threading.Thread(target=receive_messages, args=(port,))
    thread.daemon = True
    thread.start()
    input("\n[ENTER] WHO senden...\n\n")

    users = discover_users()
    known_users = parse_knownusers(users)
    #@brief funktion wird ausgeführt und return in users gespeichert, damit wir später users wiederverwenden können
    #@brief 'parse_knownusers' macht dann aus dem riesiegem f string 'users' eine handhabbares dict in java wie eine verschachtelte Hashmap
    #@brief "Alice 192.168.5.5 5000, Bob 192.168.6.6 5001" --> "Alice": ("192.168.5.5", 5000),
    print("Entdeckte Nutzer:")
    print(known_users)
    try:
        while True:
            target = input("An wen senden? (Handle): ")
            if target not in known_users:
                print("Unbekannter Nutzer.")
                continue
            text = input("Nachricht: ")
            ip, p = known_users[target]
            send_msg(ip, p, handle, text)
    
    except KeyboardInterrupt: # wird ausgelöst durch strg + c
        send_leave(handle)
        print("\nProgramm beendet.")



    

if __name__ == "__main__":
    main()