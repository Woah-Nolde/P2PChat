/*! \mainpage P2P-Chat-System - Dokumentation
\tableofcontents

\section intro Einführung
Das **P2P-Chat-System** ist eine dezentrale Chat-Anwendung, die nach dem Simple Local Chat Protocol (SLCP) arbeitet. Es ermöglicht direkte Kommunikation zwischen Peers ohne zentralen Server.

\section features Hauptfunktionen
-  Dezentrale Peer-to-Peer-Architektur
-  Textnachrichtenaustausch
-  Bildübertragung
-  Automatische Nutzererkennung
-  Abwesenheitsmodus mit Autoreply
-  Konfiguration via TOML-Datei

\section components Komponenten
\subsection cli Kommandozeileninterface (CLI)
- Benutzereingaben verarbeiten
- Nachrichten anzeigen
- Systemsteuerung

\subsection network Netzwerkschicht
- SLCP-Protokollimplementierung
- Nachrichtenverarbeitung
- Bildübertragung

\subsection discovery Discovery-Dienst
- Nutzererkennung
- Handle-Management
- Broadcast-Kommunikation

\image html architecture.png "Systemarchitektur" width=800px
*/