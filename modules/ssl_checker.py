import ssl
import socket
import datetime
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGridLayout, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from modules.base_widget import BaseModuleWidget


class SSLCheckThread(QThread):
    result = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, host: str, port: int):
        super().__init__()
        self.host = host
        self.port = port

    def run(self):
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.create_connection((self.host, self.port), timeout=10), server_hostname=self.host) as s:
                cert = s.getpeercert()
                cipher = s.cipher()
                version = s.version()

            # Parse expiry
            exp_str = cert.get("notAfter", "")
            exp_date = datetime.datetime.strptime(exp_str, "%b %d %H:%M:%S %Y %Z") if exp_str else None
            days_left = (exp_date - datetime.datetime.utcnow()).days if exp_date else None

            # Subject
            subject = dict(x[0] for x in cert.get("subject", []))
            issuer = dict(x[0] for x in cert.get("issuer", []))
            san = cert.get("subjectAltName", [])

            self.result.emit({
                "common_name": subject.get("commonName", "N/A"),
                "org": subject.get("organizationName", "N/A"),
                "issuer_cn": issuer.get("commonName", "N/A"),
                "issuer_org": issuer.get("organizationName", "N/A"),
                "not_before": cert.get("notBefore", "N/A"),
                "not_after": exp_str,
                "days_left": days_left,
                "san": ", ".join(v for _, v in san),
                "cipher": cipher[0] if cipher else "N/A",
                "tls_version": version,
                "serial": cert.get("serialNumber", "N/A"),
            })
        except ssl.SSLCertVerificationError as e:
            self.error.emit(f"Zertifikat ungültig: {e}")
        except Exception as e:
            self.error.emit(str(e))


class SSLCheckerWidget(BaseModuleWidget):
    MODULE_TITLE = "🔒 SSL Zertifikat Checker"
    MODULE_SUBTITLE = "Ablaufdatum · Aussteller · Cipher · SAN"

    def setup_ui(self):
        # Input
        row = QHBoxLayout()
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Domain, z.B. google.com oder 192.168.1.1")
        self.host_input.setStyleSheet(self.input_style())
        self.host_input.returnPressed.connect(self._check)

        port_lbl = QLabel("Port:")
        port_lbl.setStyleSheet(self.label_style())
        self.port_input = QLineEdit("443")
        self.port_input.setFixedWidth(70)
        self.port_input.setStyleSheet(self.input_style())

        self.check_btn = QPushButton("🔍  Prüfen")
        self.check_btn.setStyleSheet(self.button_style())
        self.check_btn.setFixedWidth(120)
        self.check_btn.clicked.connect(self._check)

        row.addWidget(self.host_input)
        row.addWidget(port_lbl)
        row.addWidget(self.port_input)
        row.addWidget(self.check_btn)
        self.content_layout.addLayout(row)

        # Status banner
        self.banner = QFrame()
        self.banner.setFixedHeight(56)
        self.banner.setStyleSheet("background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px;")
        banner_layout = QHBoxLayout(self.banner)
        self.banner_icon = QLabel("🔒")
        self.banner_icon.setFont(QFont("Monospace", 20))
        self.banner_text = QLabel("Noch kein Zertifikat geprüft.")
        self.banner_text.setFont(QFont("Monospace", 11))
        self.banner_text.setStyleSheet("color: #555;")
        banner_layout.addWidget(self.banner_icon)
        banner_layout.addWidget(self.banner_text)
        banner_layout.addStretch()
        self.content_layout.addWidget(self.banner)

        # Details grid
        details_frame = QFrame()
        details_frame.setStyleSheet(self.card_style())
        grid = QGridLayout(details_frame)
        grid.setContentsMargins(20, 16, 20, 16)
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)

        self._fields = {}
        rows = [
            ("Common Name", "common_name"),
            ("Organisation", "org"),
            ("Aussteller (CN)", "issuer_cn"),
            ("Aussteller (Org)", "issuer_org"),
            ("Gültig ab", "not_before"),
            ("Gültig bis", "not_after"),
            ("Verbleibende Tage", "days_left"),
            ("TLS Version", "tls_version"),
            ("Cipher Suite", "cipher"),
            ("Serial Number", "serial"),
            ("Subject Alt Names", "san"),
        ]
        for i, (label, key) in enumerate(rows):
            lbl = QLabel(f"{label}:")
            lbl.setFont(QFont("Monospace", 9))
            lbl.setStyleSheet("color: #555; background: transparent; border: none;")
            val = QLabel("—")
            val.setFont(QFont("Monospace", 9))
            val.setStyleSheet("color: #e0e0e0; background: transparent; border: none;")
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(lbl, i, 0)
            grid.addWidget(val, i, 1)
            self._fields[key] = val

        self.content_layout.addWidget(details_frame)
        self._thread = None

    def _check(self):
        host = self.host_input.text().strip()
        if not host:
            return
        try:
            port = int(self.port_input.text())
        except ValueError:
            port = 443

        self.check_btn.setEnabled(False)
        self.banner_text.setText(f"⏳ Verbinde mit {host}:{port}...")
        self.banner_text.setStyleSheet("color: #ffaa00;")

        self._thread = SSLCheckThread(host, port)
        self._thread.result.connect(self._show_result)
        self._thread.error.connect(self._show_error)
        self._thread.finished.connect(lambda: self.check_btn.setEnabled(True))
        self._thread.start()

    def _show_result(self, data: dict):
        days = data.get("days_left")
        if days is None:
            color, icon, status = "#ffaa00", "⚠️", "Ablaufdatum unbekannt"
        elif days < 0:
            color, icon, status = "#ff4444", "❌", f"ABGELAUFEN (vor {abs(days)} Tagen)"
        elif days < 14:
            color, icon, status = "#ff4444", "⚠️", f"Läuft bald ab! Noch {days} Tage"
        elif days < 30:
            color, icon, status = "#ffaa00", "⚠️", f"Läuft bald ab — noch {days} Tage"
        else:
            color, icon, status = "#00ff88", "✅", f"Gültig — noch {days} Tage"

        self.banner.setStyleSheet(f"background: {color}18; border: 1px solid {color}44; border-radius: 8px;")
        self.banner_icon.setText(icon)
        self.banner_text.setText(status)
        self.banner_text.setStyleSheet(f"color: {color}; font-family: Monospace; font-size: 11pt; font-weight: bold;")

        for key, val in data.items():
            if key in self._fields:
                text = str(val) if val is not None else "N/A"
                self._fields[key].setText(text)
                if key == "days_left" and val is not None:
                    self._fields[key].setStyleSheet(f"color: {color}; font-family: Monospace; font-size: 9pt; font-weight: bold; background: transparent; border: none;")

    def _show_error(self, msg: str):
        self.banner.setStyleSheet("background: #ff444418; border: 1px solid #ff444444; border-radius: 8px;")
        self.banner_icon.setText("❌")
        self.banner_text.setText(f"Fehler: {msg}")
        self.banner_text.setStyleSheet("color: #ff4444; font-family: Monospace;")
        for f in self._fields.values():
            f.setText("—")
