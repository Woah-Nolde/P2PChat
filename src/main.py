import socket
import threading
from network.messenger import send_msg
from network.messenger import receive_messages
from network.messenger import send_img

def send_join(handle, port):
    msg = f"JOIN {handle} {port}" 
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #@brief stelle auf socket Ebene ein, dass an die Broadcast Adresse versendet werden kann
        s.sendto(msg.encode(), ('255.255.255.255', 4000)) #@brief schicke JOIN Nachricht an Broadcast Adresse

def send_leave(handle):
    message = f"LEAVE {handle}"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(message.encode(), ('255.255.255.255', 4000))




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
    send_join(handle, port)
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