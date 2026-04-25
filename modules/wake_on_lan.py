import socket
import struct
import re
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from modules.base_widget import BaseModuleWidget
import json, os

WOL_HISTORY_FILE = os.path.expanduser("~/.fisi_toolbox_wol.json")


def send_magic_packet(mac: str, broadcast: str = "255.255.255.255", port: int = 9):
    mac_clean = re.sub(r"[^0-9a-fA-F]", "", mac)
    if len(mac_clean) != 12:
        raise ValueError("Ungültige MAC-Adresse")
    mac_bytes = bytes.fromhex(mac_clean)
    magic = b'\xff' * 6 + mac_bytes * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.connect((broadcast, port))
        s.send(magic)


class WakeOnLanWidget(BaseModuleWidget):
    MODULE_TITLE = "💡 Wake-on-LAN"
    MODULE_SUBTITLE = "Magic Packet senden · Geräte aus dem Schlaf wecken"

    def setup_ui(self):
        self._history: list[dict] = []
        self._load_history()

        # Input card
        card = QFrame()
        card.setStyleSheet(self.card_style())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(12)

        # MAC input
        mac_row = QHBoxLayout()
        mac_lbl = QLabel("MAC-Adresse:")
        mac_lbl.setStyleSheet(self.label_style())
        mac_lbl.setFixedWidth(130)
        self.mac_input = QLineEdit()
        self.mac_input.setPlaceholderText("z.B. AA:BB:CC:DD:EE:FF oder AA-BB-CC-DD-EE-FF")
        self.mac_input.setStyleSheet(self.input_style())
        mac_row.addWidget(mac_lbl)
        mac_row.addWidget(self.mac_input)
        card_layout.addLayout(mac_row)

        # Device name
        name_row = QHBoxLayout()
        name_lbl = QLabel("Gerätename:")
        name_lbl.setStyleSheet(self.label_style())
        name_lbl.setFixedWidth(130)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("z.B. Büro-PC-01 (optional)")
        self.name_input.setStyleSheet(self.input_style())
        name_row.addWidget(name_lbl)
        name_row.addWidget(self.name_input)
        card_layout.addLayout(name_row)

        # Broadcast + Port
        net_row = QHBoxLayout()
        bc_lbl = QLabel("Broadcast:")
        bc_lbl.setStyleSheet(self.label_style())
        bc_lbl.setFixedWidth(130)
        self.broadcast_input = QLineEdit("255.255.255.255")
        self.broadcast_input.setStyleSheet(self.input_style())
        port_lbl = QLabel("Port:")
        port_lbl.setStyleSheet(self.label_style())
        port_lbl.setFixedWidth(50)
        self.port_input = QLineEdit("9")
        self.port_input.setFixedWidth(70)
        self.port_input.setStyleSheet(self.input_style())
        net_row.addWidget(bc_lbl)
        net_row.addWidget(self.broadcast_input)
        net_row.addWidget(port_lbl)
        net_row.addWidget(self.port_input)
        card_layout.addLayout(net_row)

        self.content_layout.addWidget(card)

        # Send button
        btn_row = QHBoxLayout()
        self.send_btn = QPushButton("⚡  Magic Packet senden")
        self.send_btn.setStyleSheet(self.button_style())
        self.send_btn.clicked.connect(self._send)
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Monospace", 10))
        btn_row.addWidget(self.send_btn)
        btn_row.addWidget(self.status_label)
        btn_row.addStretch()
        self.content_layout.addLayout(btn_row)

        # History table
        hist_lbl = QLabel("Gespeicherte Geräte:")
        hist_lbl.setStyleSheet(self.label_style(muted=True))
        self.content_layout.addWidget(hist_lbl)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Gerätename", "MAC-Adresse", "Aktion"])
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(self.table_style())
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.content_layout.addWidget(self.table)

        self._refresh_table()

    def _send(self):
        mac = self.mac_input.text().strip()
        name = self.name_input.text().strip() or mac
        broadcast = self.broadcast_input.text().strip() or "255.255.255.255"
        try:
            port = int(self.port_input.text())
        except ValueError:
            port = 9

        try:
            send_magic_packet(mac, broadcast, port)
            self.status_label.setText(f"✅ Magic Packet gesendet an {name}")
            self.status_label.setStyleSheet("color: #00ff88; font-family: Monospace;")
            # Save to history
            existing = [d for d in self._history if d["mac"].replace(":", "").replace("-", "").upper() == re.sub(r"[^0-9a-fA-F]", "", mac).upper()]
            if not existing:
                self._history.append({"name": name, "mac": mac, "broadcast": broadcast, "port": port})
                self._save_history()
                self._refresh_table()
        except Exception as e:
            self.status_label.setText(f"❌ Fehler: {e}")
            self.status_label.setStyleSheet("color: #ff4444; font-family: Monospace;")

    def _refresh_table(self):
        self.table.setRowCount(len(self._history))
        for i, dev in enumerate(self._history):
            self.table.setItem(i, 0, QTableWidgetItem(dev.get("name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(dev.get("mac", "")))
            btn = QPushButton("⚡ Wecken")
            btn.setStyleSheet(self.button_style())
            btn.clicked.connect(lambda _, d=dev: self._send_saved(d))
            self.table.setCellWidget(i, 2, btn)

    def _send_saved(self, dev: dict):
        try:
            send_magic_packet(dev["mac"], dev.get("broadcast", "255.255.255.255"), dev.get("port", 9))
            self.status_label.setText(f"✅ Magic Packet gesendet an {dev['name']}")
            self.status_label.setStyleSheet("color: #00ff88; font-family: Monospace;")
        except Exception as e:
            self.status_label.setText(f"❌ Fehler: {e}")
            self.status_label.setStyleSheet("color: #ff4444; font-family: Monospace;")

    def _load_history(self):
        try:
            if os.path.exists(WOL_HISTORY_FILE):
                with open(WOL_HISTORY_FILE) as f:
                    self._history = json.load(f)
        except Exception:
            self._history = []

    def _save_history(self):
        try:
            with open(WOL_HISTORY_FILE, "w") as f:
                json.dump(self._history, f, indent=2)
        except Exception:
            pass
