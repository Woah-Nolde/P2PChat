/*! \page protocol SLCP-Implementierung
\section formats Nachrichtenformate

\subsection join JOIN
\code{.unparsed}
JOIN <Handle> <Port>
\endcode
Beispiel: `JOIN Alice 5000`

\subsection msg MSG
\code{.unparsed}
MSG <Handle> <Text>
\endcode
Beispiel: `MSG Bob Hallo%20Welt`

\subsection img IMG
\code{.unparsed}
IMG <Handle> <Size>
[Binärdaten...]
\endcode

\section sequence Beispielabläufe
\subsection discovery Nutzererkennung
\startuml
participant "Neuer Client" as C
participant "Discovery" as D

C -> D : JOIN Alice 5000
C -> D : WHO
D --> C : KNOWUSERS Bob 192.168.1.2 5001
enduml

\subsection messaging Nachrichtenaustausch
\startuml
participant Alice
participant Bob

Alice -> Bob : MSG Bob "Hallo"
Bob --> Alice : MSG Alice "Hi!"
enduml

\section ports Portverwendung
| Port | Typ      | Verwendung                     |
|------|----------|--------------------------------|
| 4000 | UDP      | Discovery-Broadcast            |
| 4001 | UDP      | Discovery-Events               |
| 5000+ | UDP     | Client-Kommunikation           |
*/