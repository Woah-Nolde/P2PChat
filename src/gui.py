import socket
import threading
import time
import os
import sys
from multiprocessing import Process, Queue
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QDialog,
    QInputDialog,
    QFileDialog,
    QListWidget,     # <-- Hier hinzufügen
)
from PyQt5.QtCore import QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QPixmap, QTextCursor

from config_manager import load_config, save_config, edit_config
from discovery import discoveryloop
from messenger import network_main

# Hilfsfunktion aus main.py, um eigenen IP zu bekommen
def get_own_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def send_join(handle, port):
    msg = f"JOIN {handle} {port}"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(msg.encode(), ('255.255.255.255', 4000))


def send_leave(handle, whoisport, known_users):
    message = f"LEAVE {handle}"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(message.encode(), ('255.255.255.255', whoisport))

    for h, (ip, port) in known_users.items():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(message.encode(), (ip, port))


def find_free_port(start_port, end_port):
    for port in range(start_port, end_port + 1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"Kein freier UDP-Port im Bereich {start_port}-{end_port} gefunden!")


class ReaderThread(QThread):
    new_log = pyqtSignal(str)
    update_users = pyqtSignal(dict)
    update_handle = pyqtSignal(str)
    abwesend_mode = pyqtSignal(bool)

    def __init__(self, disc_to_ui, net_to_ui, ui_to_net, handle, port):
        super().__init__()
        self.disc_to_ui = disc_to_ui
        self.net_to_ui = net_to_ui
        self.ui_to_net = ui_to_net
        self.handle = handle
        self.port = port
        self.abwesend = False
        self.known_users = {}

    def run(self):
        while True:
            # Handle network messages
            if not self.net_to_ui.empty():
                msg = self.net_to_ui.get()
                typ = msg.get("type")

                if typ == "condition":
                    # Eventuell für Abwesenheitsmodus etc.
                    pass

                elif typ == "HANDLE_UPDATE":
                    if int(msg.get("port")) == self.port:
                        new_handle = msg.get("new_handle")
                        self.handle = new_handle
                        self.update_handle.emit(new_handle)
                        self.new_log.emit(f"[Discovery] Dein Name war vergeben. Neuer Name: {new_handle}")

                elif typ == "LEAVE":
                    h = msg.get("handle")
                    if h == self.handle:
                        # eigene LEAVE ignorieren
                        continue
                    if h in self.known_users:
                        del self.known_users[h]
                        self.update_users.emit(self.known_users)
                    self.new_log.emit(f"[Discovery] {h} hat den Chat verlassen.")

                elif typ == "JOIN":
                    h = msg.get("handle")
                    ip = msg.get("ip")
                    p = msg.get("port")
                    if h == self.handle and get_own_ip() == ip:
                        continue  # Eigene JOIN-Nachricht ignorieren
                    self.known_users[h] = (ip, p)
                    self.update_users.emit(self.known_users)
                    self.new_log.emit(f"[Discovery] {h} ist online ({ip}:{p})")

                elif typ == "WHO_RESPONSE":
                    users = msg.get("users", {})
                    self.known_users = users
                    self.update_users.emit(users)
                    if not users or (len(users) == 1 and self.handle in users):
                        self.new_log.emit("Niemand online, außer dir!")
                    else:
                        user_list = ", ".join(users.keys())
                        self.new_log.emit(f"Entdeckte Nutzer: {user_list}")

                elif typ == "recv_msg":
                    sender = msg.get("sender")
                    text = msg.get("text")

                    if self.abwesend:
                        # Autoreply senden, wenn Nutzer bekannt
                        if sender in self.known_users:
                            ip, port = self.known_users[sender]
                            self.ui_to_net.put({
                                "type": "MSG",
                                "text": "Ich bin gerade abwesend, melde mich später!",
                                "target_ip": ip,
                                "target_port": port,
                                "handle": self.handle
                            })
                        else:
                            self.new_log.emit("[Abwesend-Modus] Unbekannter Nutzer, Autoreply nicht möglich.")
                        # **Nachricht nicht anzeigen!**
                        continue

                    # Nachricht anzeigen, wenn nicht abwesend
                    self.new_log.emit(f"[Nachricht] von {sender}: {text}")

                elif typ == "recv_img":
                    sender = msg.get("sender")
                    b64_data = msg.get("data")
                    filename = msg.get("filename", "image")

                    import base64
                    from PyQt5.QtGui import QPixmap

                    img_data = base64.b64decode(b64_data)
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_data)

                    if not pixmap.isNull():
                        # Bild in Base64 als Data-URI für HTML einbetten (Thumbnailbreite 200px)
                        b64_img = base64.b64encode(img_data).decode('utf-8')
                        img_html = f'<br><b>Bild von {sender} empfangen: {filename}</b><br>'
                        img_html += f'<img src="data:image/png;base64,{b64_img}" width="200"><br>'
                        self.new_log.emit(img_html)
                    else:
                        self.new_log.emit(f"[Bild von {sender} konnte nicht geladen werden]")

                elif typ == "TXT":
                    sender = msg.get("handle", "System")
                    text = msg.get("text", "")
                    self.new_log.emit(f"[{sender}] {text}")

                else:
                    # Andere Nachrichten evtl. hier behandeln
                    pass

            # Discovery-Nachrichten
            if not self.disc_to_ui.empty():
                msg = self.disc_to_ui.get()
                if msg.get("type") == "singleton":
                    self.new_log.emit(msg.get("text"))

            time.sleep(0.1)  # CPU schonen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("P2P Chat GUI")
        self.resize(700, 500)

        self.abwesend = False
        self.known_users = {}
        self.handle = None
        self.whoisport = None
        self.port = None

        # Queues und Prozesse
        self.ui_to_net = Queue()
        self.net_to_ui = Queue()
        self.net_to_disc = Queue()
        self.disc_to_net = Queue()
        self.disc_to_ui = Queue()

        self.network_process = None
        self.discovery_process = None
        self.reader_thread = None

        self._setup_ui()
        self.apply_style()
        self._load_config_and_start()

    def apply_style(self):
        style = """
        QWidget {
            background-color: #e6f0fa;  /* sehr helles Blau */
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 12pt;
            color: #222222;
        }

        QTextEdit {
            background-color: #ffffff;
            border: 1px solid #a0bcd6;
            border-radius: 8px;
            padding: 8px;
        }

        QListWidget {
            background-color: #ffffff;
            border: 1px solid #a0bcd6;
            border-radius: 8px;
        }

        QPushButton {
            background-color: #0088cc;
            color: white;
            border: none;
            padding: 6px 14px;
            border-radius: 6px;
            font-weight: 600;
            transition: background-color 0.3s ease;
        }

        QPushButton:hover {
            background-color: #005f99;
        }

        QPushButton:pressed {
            background-color: #003f66;
        }

        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #a0bcd6;
            border-radius: 6px;
            padding: 6px;
            selection-background-color: #66aaff;
        }

        QLabel {
            font-weight: bold;
            color: #005f99;
        }
        """
        self.setStyleSheet(style)

    def choose_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Bild auswählen",
            "",
            "Bilder (*.png *.jpg *.jpeg *.bmp *.gif);;Alle Dateien (*)",
            options=options
        )
        if file_path:
            self.input_message.setText(file_path)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        vbox = QVBoxLayout()

        # Chat-Log
        self.chat_log = QTextEdit()
        self.chat_log.setReadOnly(True)
        vbox.addWidget(self.chat_log)

        # Userliste (ähnlich 'users' Befehl)
        h_users = QHBoxLayout()
        self.user_list_widget = QListWidget()
        h_users.addWidget(QLabel("Bekannte Nutzer:"))
        h_users.addWidget(self.user_list_widget)
        vbox.addLayout(h_users)

        # Eingabezeile
        h_input = QHBoxLayout()
        self.input_handle = QLineEdit()
        self.input_handle.setPlaceholderText("Handle")
        self.input_handle.setFixedWidth(120)

        self.input_message = QLineEdit()
        self.input_message.setPlaceholderText("Nachricht / Pfad")

        self.send_msg_btn = QPushButton("Nachricht senden")
        self.send_msg_btn.clicked.connect(self.send_message)

        self.send_img_btn = QPushButton("Bild senden")
        self.send_img_btn.clicked.connect(self.choose_image)

        h_input.addWidget(self.input_handle)
        h_input.addWidget(self.input_message)
        h_input.addWidget(self.send_msg_btn)
        h_input.addWidget(self.send_img_btn)
        vbox.addLayout(h_input)

        # Steuerbuttons
        h_buttons = QHBoxLayout()
        self.btn_who = QPushButton("Who")
        self.btn_who.clicked.connect(self.send_who)

        self.btn_users = QPushButton("Users anzeigen")
        self.btn_users.clicked.connect(self.show_users)

        self.btn_name = QPushButton("Name ändern")
        self.btn_name.clicked.connect(self.change_name)

        self.btn_config = QPushButton("Config bearbeiten")
        self.btn_config.clicked.connect(self.edit_config_popup)

        self.btn_reload = QPushButton("Config neu laden")
        self.btn_reload.clicked.connect(self.reload_config)

        self.btn_abwesend = QPushButton("Abwesend ein/aus")
        self.btn_abwesend.clicked.connect(self.toggle_abwesend)

        self.btn_quit = QPushButton("Beenden")
        self.btn_quit.clicked.connect(self.quit_chat)

        for btn in [self.btn_who, self.btn_users, self.btn_name, self.btn_config, self.btn_reload, self.btn_abwesend, self.btn_quit]:
            h_buttons.addWidget(btn)

        vbox.addLayout(h_buttons)

        central_widget.setLayout(vbox)

    def _load_config_and_start(self):
        # Laden der Konfiguration
        config = load_config()
        self.handle = config["user"]["handle"]
        self.whoisport = int(config["network"]["whoisport"])
        port_range = config["network"]["port_range"]
        self.port = find_free_port(port_range[0], port_range[1])

        self.log(f"Starte Chat mit Handle '{self.handle}' auf Port {self.port} (Discovery Port: {self.whoisport})")

        # Start Netzwerkprozess
        self.network_process = Process(target=network_main, args=(
            self.ui_to_net, self.net_to_ui, self.net_to_disc, self.disc_to_net, self.port))
        self.network_process.start()

        # Reader Thread für Nachrichten anzeigen
        self.reader_thread = ReaderThread(
            self.disc_to_ui, self.net_to_ui, self.ui_to_net, self.handle, self.port)
        self.reader_thread.new_log.connect(self.log)
        self.reader_thread.update_users.connect(self.update_known_users)
        self.reader_thread.update_handle.connect(self.update_handle)
        self.reader_thread.start()

        # Discovery Prozess
        self.discovery_process = Process(target=discoveryloop, args=(
            self.net_to_disc, self.disc_to_net, self.disc_to_ui, self.whoisport), daemon=True)
        self.discovery_process.start()

        time.sleep(0.2)

        send_join(self.handle, self.port)

    def log(self, text):
        if "<img" in text or "<b>" in text or "<br>" in text:
            # HTML einfügen
            self.chat_log.moveCursor(QTextCursor.End)
            self.chat_log.insertHtml(text)
            self.chat_log.insertHtml("<br>")  # Zeilenumbruch ergänzen
            self.chat_log.ensureCursorVisible()
        else:
            self.chat_log.append(text)

    def update_known_users(self, users):
        self.known_users = users
        self.user_list_widget.clear()
        for h, (ip, port) in users.items():
            self.user_list_widget.addItem(f"{h} ({ip}:{port})")

    def update_handle(self, new_handle):
        self.handle = new_handle
        self.log(f"Dein neuer Name ist: {new_handle}")

    # GUI-Befehle analog CLI

    def send_who(self):
        self.ui_to_net.put({"type": "WHO"})

    def show_users(self):
        if not self.known_users:
            self.log("Keine bekannten Nutzer.")
        else:
            users_str = ", ".join(self.known_users.keys())
            self.log(f"Bekannte Nutzer: {users_str}")

    def send_message(self):
        target = self.input_handle.text().strip()
        text = self.input_message.text().strip()

        if not target:
            self.log("Bitte Ziel-Handle eingeben.")
            return
        if not text:
            self.log("Bitte eine Nachricht eingeben.")
            return

        if target not in self.known_users:
            self.log(f"Unbekannter Nutzer: {target}")
            return

        ip, port = self.known_users[target]

        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        MAX_IMAGE_SIZE = 50 * 1024  # 50 KB

        if os.path.isfile(text) and text.lower().endswith(image_extensions):
            size = os.path.getsize(text)
            if size > MAX_IMAGE_SIZE:
                self.log(f"[Fehler] Bild zu groß ({size} Bytes). Maximal erlaubt: {MAX_IMAGE_SIZE} Bytes.")
                return

            pixmap = QPixmap(text)
            if not pixmap.isNull():
                scaled = pixmap.scaledToWidth(200)  # Thumbnailgröße
                cursor = self.chat_log.textCursor()
                cursor.movePosition(cursor.End)
                self.chat_log.insertHtml(f"<br><b>Bild an {target} gesendet:</b><br>")
                self.chat_log.document().addResource(1, QUrl(text), scaled)
                self.chat_log.insertHtml(f'<img src="{text}"><br>')
                self.chat_log.ensureCursorVisible()

            import base64
            with open(text, "rb") as img_file:
                b64_data = base64.b64encode(img_file.read()).decode('utf-8')

            self.ui_to_net.put({
                "type": "IMG",
                "IP": ip,
                "PORT": port,
                "PFAD": text,
                "HANDLE": self.handle,
            })

            self.input_message.clear()
            return

        # Textnachricht senden
        self.ui_to_net.put({
            "type": "MSG",
            "text": text,
            "target_ip": ip,
            "target_port": port,
            "handle": self.handle
        })

        self.log(f"[Du an {target}]: {text}")
        self.input_message.clear()

    def change_name(self):
        new_handle, ok = QInputDialog.getText(self, "Name ändern", "Neuer Name:")
        if ok and new_handle:
            if new_handle == self.handle:
                self.log("Das ist bereits dein Name.")
                return

            send_leave(self.handle, int(self.whoisport), self.known_users)
            self.handle = new_handle
            save_config({"user": {"handle": self.handle}}, "config.toml")
            send_join(self.handle, self.port)
            self.log(f"Name geändert zu: {self.handle}")

    def edit_config_popup(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox, QMessageBox
        from config_manager import load_config, save_config

        config = load_config()

        dlg = QDialog(self)
        dlg.setWindowTitle("Konfiguration bearbeiten")

        layout = QFormLayout()

        handle_input = QLineEdit(config["user"].get("handle", ""))
        autoreply_input = QLineEdit(config["user"].get("autoreply", ""))
        port_input = QSpinBox()
        port_input.setMaximum(65535)
        port_input.setValue(int(config["network"].get("port", 12345)))
        discovery_input = QLineEdit(config["network"].get("discovery", ""))

        layout.addRow("Handle:", handle_input)
        layout.addRow("Autoreply:", autoreply_input)
        layout.addRow("Port:", port_input)
        layout.addRow("Discovery:", discovery_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        dlg.setLayout(layout)

        def save():
            try:
                config["user"]["handle"] = handle_input.text()
                config["user"]["autoreply"] = autoreply_input.text()
                config["network"]["port"] = port_input.value()
                config["network"]["discovery"] = discovery_input.text()
                save_config(config)
                self.log("Konfiguration gespeichert.")
                dlg.accept()
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Speichern fehlgeschlagen:\n{e}")

        button_box.accepted.connect(save)
        button_box.rejected.connect(dlg.reject)

        dlg.exec_()

    def edit_config(self):
        edit_config()
        self.log("Config bearbeitet.")

    def reload_config(self):
        config = load_config()
        self.log("Config neu geladen.")
        # Optional: Config aktualisieren im Programm, z.B. Handle, Whoisport usw.

    def toggle_abwesend(self):
        self.abwesend = not self.abwesend
        if self.abwesend:
            self.log("Abwesend-Modus aktiviert.")
        else:
            self.log("Abwesend-Modus deaktiviert.")
        # ReaderThread informieren:
        if self.reader_thread:
            self.reader_thread.abwesend = self.abwesend

    def quit_chat(self):
        send_leave(self.handle, self.whoisport, self.known_users)

        if self.network_process and self.network_process.is_alive():
            self.network_process.terminate()
            self.network_process.join()

        if self.discovery_process and self.discovery_process.is_alive():
            self.discovery_process.terminate()
            self.discovery_process.join()

        self.log("Chat beendet.")
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())