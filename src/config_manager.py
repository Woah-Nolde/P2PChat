## @file config_manager.py
# @brief Verwaltet die TOML-Konfigurationsdatei


import tomllib
import tomli_w 
import os
import socket

known_users = {}
conf_file = "config.toml"

## @brief Lädt die Konfiguration aus einer TOML-Datei
def load_config(path=conf_file):   # @param path Pfad zur Konfigurationsdatei
    if not os.path.exists(path):   # @return Konfiguration als Dictionary
       print(f"Warnung: Konfigurationsdatei '{path}' nicht gefunden.") # @exception FileNotFoundError, Wenn Datei nicht existiert
       return {}
    with open(path, "rb") as f:  
        return tomllib.load(f)  


## @brief Speichert die Konfiguration in eine TOML-Datei
def save_config(config, path=conf_file):  
    with open(path, "wb") as f:
        tomli_w.dump(config, f)  
        print(f"Konfiguration gespeichert in '{path}'.")


## @brief Zeigt die aktuelle Konfiguration an
def show_config(config):
    print("Aktuelle Konfiguration:")
    for sections, value in config.items():
        print(f"[{sections}]")
        for key, val in value.items():
            print(f"  {key} = {val}")


## @brief Konvertiert TOML-Werte zu Python-Typen
def parse_toml_type(value):  # @param value aus TOML
    if value.lower() in ["true",  "false"]:
        return value.lower() == "true" 
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value
        # @details Automatische Erkennung von:
# - Boolean ("true"/"false")
# - Integer (z.B. "5000")
# - Float (z.B. "3.14")
# - String (Fallback)


## @brief Konfigurationsbearbeitung        
def edit_config(): 
    config = load_config() 
    show_config(config)  # @return Konfiguration als Dictionary
    sections = {
        '1': ('user', 'Benutzereinstellungen'),
        '2': ('network', 'Netzwerkeinstellungen'),
        '3': ('storage', 'Speichereinstellungen')
    }

    while True:
        print("\nKonfiguration bearbeiten:")
        print("1. Benutzereinstellungen (Handle, Autoreply)")
        print("2. Netzwerkeinstellungen (Ports, Discovery)")
        print("3. Speichereinstellungen (Bildpfad)")
        print("0. Zurück")

        # @details
# Bietet eine menügeführte Oberfläche zur Bearbeitung aller Konfigurationsparameter:
# - Benutzereinstellungen (Handle, Autoreply)
# - Netzwerkeinstellungen (Portbereich, Discovery-Port)
# - Speichereinstellungen (Bildpfad)

        choice = input("Auswahl: ").strip()
        if choice == '0':
            return config

        if choice in sections:
            section, desc = sections[choice]
            print(f"\n{desc}:")
            for key in config.get(section, {}):
                print(f"  {key}: {config[section][key]}")
            
            key = input("\nZu ändernder Schlüssel (leer=lassen): ").strip()
            if key and key in config[section]:
                new_value = input(f"Neuer Wert für {key} ({type(config[section][key]).__name__}): ").strip()
                try:
                    # Automatische Typkonvertierung
                    if isinstance(config[section][key], bool):
                        config[section][key] = new_value.lower() in ('true', '1', 'ja')
                    elif isinstance(config[section][key], int):
                        config[section][key] = int(new_value)
                    else:
                        config[section][key] = new_value
                except ValueError:
                    print("Fehler: Ungültiger Wert!")
        else:
            print("Ungültige Auswahl!")
    save_config(config)  # Speichert die Änderungen in der Konfigurationsdatei
# @exception ValueError Bei ungültigen Typkonvertierungen
# @note Für Netzwerkänderungen ist ein Neustart erforderlich


## @brief Sucht einen Nutzer in known_users
def lookup_handle(handle, config=None): # @param handle Zu suchender Handle (None für gesamte Liste)
    return known_users if handle is None else known_users.get(handle)


## @brief Speichert ein empfangenes Bild
def save_image(handle, data): 
    config = load_config()
    os.makedirs(config["storage"]["imagepath"], exist_ok=True)
    path = os.path.join(config["storage"]["imagepath"], f"{handle}.jpg")
    with open(path, "wb") as f:
        f.write(data)
    print(f"Bild von {handle} gespeichert unter {path}")


## @brief Sendet eine Autoreply-Nachricht an den Absender
def handle_autoreply(sender_ip, sender_port, config):
    if config["user"]["autoreply"]:
        reply_msg = f"MSG {config['user']['handle']} {config['user']['autoreply']}\n"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(reply_msg.encode(), (sender_ip, sender_port))