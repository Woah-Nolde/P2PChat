import tomllib
import tomli_w 
import os

known_users = {}
conf_file = "config/config.toml"


def load_config(path=conf_file):
    if not os.path.exists(path):
       print(f"Warnung: Konfigurationsdatei '{path}' nicht gefunden.")
       return {}
    with open(path, "rb") as f:
        return tomllib.load(f)

def save_config(config, path=conf_file):
    with open(path, "wb") as f:
        tomli_w.dump(config, f)
        print(f"Konfiguration gespeichert in '{path}'.")

def show_config(config):
    print("Aktuelle Konfiguration:")
    for sections, value in config.items():
        print(f"[{sections}]")
        for key, val in value.items():
            print(f"  {key} = {val}")

def parse_toml_type(value):
    if value.lowe() in ["true",  "false"]:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value
        
def edit_config():
    config = load_config()
    show_config(config)
    section = input("Wähle eine Sektion zum Bearbeiten): ").strip()
    if section not in config:
        config[section] = {}
    key = input(f"Feld zum Bearbeiten in [{section}]: ").strip()
    value = input(f"Neuer Wert für [{section}]{key}: ").strip()
    config[section][key] = parse_toml_type(value)
    save_config(config)

def lookup_handle(handle, config=None):
    return known_users if handle is None else known_users.get(handle)

def save_image(handle, data):
    config = load_config()
    os.makedirs(config["storage"]["imagepath"], exist_ok=True)
    path = os.path.join(config["storage"]["imagepath"], f"{handle}.jpg")
    with open(path, "wb") as f:
        f.write(data)
    print(f"Bild von {handle} gespeichert unter {path}")