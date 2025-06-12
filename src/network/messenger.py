
#import socket

#def receive_messages(my_port):

    #@brief Empfängt kontinuierlich UDP-Nachrichten auf einem bestimmten Port und zeigt sie an.
    
    
 #   sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP Socket erstellen


  #  sock.bind(('', my_port)) 

     #@brief Binde den Socket an alle verfügbaren Netzwerkschnittstellen ('')
    #@brief und den angegebenen Port
    #@brief '' bedeutet "alle verfügbaren Netzwerkinterfaces"

   # print(f"[Empfänger] Lausche auf Port {my_port} für eingehende Nachrichten...")

    #while True:
     #   data, addr = sock.recvfrom(1024)
            #@brief Warte auf eingehende Nachricht 
            #@brief recvfrom gibt zurück:
            #@brief data: die empfangenen Bytes (max. 1024 Bytes)
            #@brief addr: IP-Adresse des Absenders


      #  message = data.decode()
        #@brief Dekodiere die empfangenen Bytes zu einem String 

         
       # print(f"\n[Nachricht von {addr}] {message}\n> ", end="")



#def send_msg(target_ip, target_port, sender_handle, text):
    #@brief Sendet eine Textnachricht per UDP an einen bestimmten Empfänger
    #@brief target_ip (str): IP-Adresse des Zielrechners
    #@brief target_port (int): Portnummer des Zielservices
    #@brief sender_handle (str): Absenderkennung
    #@brief text (str): Der zu sendende Nachrichtentext

    

 #   msg = f"MSG: {sender_handle} {text}"
    #@brief MSG: Absender Nachrichtentext"


  #  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:


   #     s.sendto(msg.encode(), (target_ip, target_port))
        #@brief Sende die Nachricht an den Zielrechner
            #@brief encode() wandelt den String in Bytes um
    
# messenger.py
import socket
import os

# NEU: SLCP-Protokoll-Parser
def parse_slcp(message):
    if message.startswith("MSG:"):
        parts = message[4:].split(" ", 1)
        if len(parts) == 2:
            sender = parts[0]
            text = parts[1].replace("%20", " ")  # Maskierung auflösen
            return ("MSG", sender, text)
    return ("UNKNOWN", None, message)



def receive_messages(my_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', my_port))
    print(f"[Empfänger] Lausche auf Port {my_port} für eingehende Nachrichten...")

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
                print(f"\n[Nachricht von {sender}] {text}\n> ", end="")
            else:
                print(f"\n[Unbekanntes Format] {message}\n> ", end="")



def send_msg(target_ip, target_port, sender_handle, text):
    text_masked = text.replace(" ", "%20")
    msg = f"MSG:{sender_handle} {text_masked}"
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

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(message, (target_ip, target_port))
    print(f"[Sender] Bild {filename} an {target_ip}:{target_port} gesendet.")
