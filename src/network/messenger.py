
import socket

def receive_messages(my_port):

    #@brief Empfängt kontinuierlich UDP-Nachrichten auf einem bestimmten Port und zeigt sie an.
    
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP Socket erstellen


    sock.bind(('', my_port)) 

     #@brief Binde den Socket an alle verfügbaren Netzwerkschnittstellen ('')
    #@brief und den angegebenen Port
    #@brief '' bedeutet "alle verfügbaren Netzwerkinterfaces"

    print(f"[Empfänger] Lausche auf Port {my_port} für eingehende Nachrichten...")

    while True:
        data, addr = sock.recvfrom(1024)
            #@brief Warte auf eingehende Nachricht 
            #@brief recvfrom gibt zurück:
            #@brief data: die empfangenen Bytes (max. 1024 Bytes)
            #@brief addr: IP-Adresse des Absenders


        message = data.decode()
        #@brief Dekodiere die empfangenen Bytes zu einem String 

         
        print(f"\n[Nachricht von {addr}] {message}\n> ", end="")



def send_msg(target_ip, target_port, sender_handle, text):
    #@brief Sendet eine Textnachricht per UDP an einen bestimmten Empfänger
    #@brief target_ip (str): IP-Adresse des Zielrechners
    #@brief target_port (int): Portnummer des Zielservices
    #@brief sender_handle (str): Absenderkennung
    #@brief text (str): Der zu sendende Nachrichtentext

    

    msg = f"MSG: {sender_handle} {text}"
    #@brief MSG: Absender Nachrichtentext"


    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:


        s.sendto(msg.encode(), (target_ip, target_port))
        #@brief Sende die Nachricht an den Zielrechner
            #@brief encode() wandelt den String in Bytes um
    
