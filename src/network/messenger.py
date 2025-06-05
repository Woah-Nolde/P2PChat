
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


def receive_messages(my_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', my_port))
    print(f"[Empfänger] Lausche auf Port {my_port} für eingehende Nachrichten...")

    while True:
        data, addr = sock.recvfrom(65507)

        if data.startswith(b"IMG:"):
            parts = data.split(b":", 3)
            filename = parts[1].decode()
            size = int(parts[2].decode())
            image_data = parts[3]

            with open("empfangen_" + filename, "wb") as f:
                f.write(image_data)
            print(f"[Empfänger] Bild empfangen von {addr} → gespeichert als empfangen_{filename}")

        else:
            message = data.decode()
            print(f"\n[Nachricht von {addr}] {message}\n> ", end="")


def send_msg(target_ip, target_port, sender_handle, text):
    msg = f"MSG: {sender_handle} {text}"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(msg.encode(), (target_ip, target_port))


def send_img(target_ip, target_port, filename):
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
