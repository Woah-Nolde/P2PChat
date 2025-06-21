/*! \page architecture Systemarchitektur
\section design Entwurfsprinzipien
Das System folgt einem **3-Schichten-Modell** mit klar getrennten Verantwortlichkeiten:

1. **Präsentationsschicht** (CLI)
2. **Netzwerkschicht** (Messenger)
3. **Service-Schicht** (Discovery)

\section communication Prozesskommunikation
\startuml
title IPC-Kommunikation
[CLI] -> [Netzwerk] : "send <user> <msg>"
[Netzwerk] -> [Discovery] : "WHO"
[Discovery] -> [Netzwerk] : "KNOWUSERS"
[Netzwerk] -> [CLI] : "recv_msg"
enduml

\section data Datenfluss
\subsection outbound Ausgehende Nachrichten
1. CLI erfasst Nutzereingabe
2. Netzwerkschicht formatiert nach SLCP
3. UDP-Sendevorgang

\subsection inbound Eingehende Nachrichten
1. Netzwerk empfängt UDP-Paket
2. Nachricht wird geparst
3. CLI zeigt Inhalt an

\section concurrency Parallelverarbeitung
| Komponente    | Thread/Prozess | Beschreibung               |
|---------------|----------------|----------------------------|
| CLI           | Hauptthread    | Blockierende Eingabe        |
| Netzwerk      | Subprozess     | Kontinuierlicher Empfang    |
| Discovery     | Subprozess     | Broadcast-Handling          |
*/