/*! \page usage Bedienungsanleitung
\section installation Installation
\code{.sh}
# Voraussetzungen
sudo apt install python3 python3-pip

# Projekt klonen
git clone https://github.com/ihr-repo/p2p-chat.git
cd p2p-chat

# Abhängigkeiten installieren
pip install -r requirements.txt
\endcode

\section configuration Konfiguration
Bearbeiten Sie `config/config.toml`:
```toml
[user]
handle = "Ihr_Name"
autoreply = "Ich bin nicht verfügbar"

[network]
whoisport = 4000
port_range = [5000, 5050]