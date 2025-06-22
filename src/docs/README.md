# BSRN Projekt – Peer-to-Peer Chat (SLCP)

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Architecture](https://img.shields.io/badge/arch-3%20processes-orange)

Ein dezentrales Chat-System mit Text-/Bildunterstützung, entwickelt für das Modul "Betriebssysteme und Rechnernetze" an der UAS.

---

## Installation
```bash
# Voraussetzungen
sudo apt install python3 python3-pip

# Repository klonen
git clone https://github.com/Woah-Nolde/P2PChat
cd p2p-chat

# Abhängigkeiten installieren
pip install -r requirements.txt
```

---

## Konfiguration
Bearbeiten Sie `config.toml`:
```toml
handle = "Ihr_Name"
port = 5000          # Client-zu-Client-Port
whoisport = 4000     # Discovery-Broadcast-Port
autoreply = "Abwesend"
imagepath = "./received_images"
```

---

## Systemarchitektur
```mermaid
graph TD
    A[main.py\nCLI-UI] <-->|IPC/Queues| B[messenger.py\nNetzwerk]
    B <-->|UDP Broadcast/IPC| C[discovery.py]
    B -->|Unicast| D[Andere Clients]
    A <-->|read/write| E[config.toml]
```

**Prozessaufteilung**:
| Prozess          | Verantwortlichkeit               | Protokolle          |
|------------------|----------------------------------|---------------------|
| `main.py`        | Nutzerinteraktion                | IPC/Broadcast (Sockets/Queues) |
| `messenger.py`   | Nachrichtenaustausch             | UDP/IPC Unicast/Broadcast |
| `discovery.py`   | Teilnehmererkennung              | UDP/IPC Broadcast       |

---

## Bedienung
**Starten**:
```bash
python3 main.py
```

**CLI-Befehle**:
| Befehl          | Aktion                           | Beispiel            |
|-----------------|----------------------------------|---------------------|
| `/who`          | Aktive Nutzer anzeigen           | `/Entdeckte Nutzer: Alice`              |
| `/send <user> <text>` | Nachricht senden          | `/send Bob Hallo!`   |
| `/img <user> <path>` | Bild senden               | `/img Bob ~/pic.jpg`|
| `/quit`        | Chat verlassen                   | `/Alice hat den Chat verlassen`            |
| `/abwesend`        | [Abwesend-Modus]                   | `/Abwesend-Modus`            |


---

## Protokoll (SLCP)
| Befehl       | Format                          | Beispiel             |
|--------------|---------------------------------|----------------------|
| `JOIN`       | `JOIN <handle> <port>`          | `JOIN Alice 5000`    |
| `LEAVE`      | `LEAVE <handle>`                | `LEAVE Alice`        |
| `MSG`        | `MSG <handle> <text>`           | `MSG Bob "Hallo"`    |
| `IMG`        | `IMG <handle> <size>` + Binärdaten | `IMG Bob 2048`    |

---

## Dokumentation
- Code-Dokumentation: Generieren mit `doxygen Doxyfile`
- Protokollspezifikation: Siehe Projektunterlagen

---

## Team
| Name             | Rolle                | Komponente          |
|------------------|----------------------|---------------------|
| Team-Mitglied 1  | Netzwerkschicht      | messenger.py        |
| Team-Mitglied 2  | Discovery-Dienst     | discovery.py        |
| Team-Mitglied 3  | Benutzeroberfläche   | main.py             |


## Logo
<p align="center">
  <img src=".src/image/Logo/Logo.png" alt="Projektlogo" width="250" />
</p>

## Screenshot der CLI
![CLI-Benutzeroberfläche](.src/image/BSRN_Screenshots/Screenshot_1.jpg)
![CLI-Benutzeroberfläche](.src/image/BSRN_Screenshots/Screenshot_2.jpg)
![CLI-Benutzeroberfläche](.src/image/BSRN_Screenshots/Screenshot_3.jpg)
![CLI-Benutzeroberfläche](.src/image/BSRN_Screenshots/Screenshot_4.jpg)
![CLI-Benutzeroberfläche](.src/image/BSRN_Screenshots/Screenshot_5jpg)
![CLI-Benutzeroberfläche](.src/image/BSRN_Screenshots/Screenshot_6.jpg)

*Lizenz: MIT – Frankfurt University of Applied Sciences, 2025*
```
