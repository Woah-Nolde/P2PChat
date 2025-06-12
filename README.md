# BSRN Projekt fra uas
Dieses Repository wurde für ein Chatprogramm als Peer-to-Peer-System angelegt.
/**
@mainpage Chat-Programm - Technische Dokumentation

@section intro Einführung
Dieses Projekt implementiert ein dezentrales Chat-System auf Basis des SLCP-Protokolls.
Ziel ist die einfache Übertragung von Text- und Bildnachrichten über ein lokales Netzwerk.

@section arch Architektur
Das System besteht aus drei Hauptkomponenten:
- Discovery-Dienst (broadcast.py)
- Netzwerkkommunikation (messenger.py)
- Benutzerschnittstelle (main.py oder cli.py)

@section usage Bedienung
1. Start über `main.py` oder `cli.py`
2. WHO-Abfrage zur Teilnehmererkennung
3. Senden von Nachrichten oder Bildern über die CLI

@section config Konfiguration
Die Datei `config.toml` enthält:
- Benutzername (handle)
- UDP-Portbereich (port)
- Broadcast-Port (whoisport)
- Autoreply-Text
- Bild-Speicherpfad (imagepath)

@section protocol Protokoll (SLCP)
Implementiert werden:
- JOIN, LEAVE, WHO, KNOWUSERS, MSG, IMG
Details: siehe SLCP-Spezifikation.

*/
