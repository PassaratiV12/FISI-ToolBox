import subprocess
import socket
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from modules.base_widget import BaseModuleWidget


class CommandThread(QThread):
    output = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, cmd: list[str]):
        super().__init__()
        self.cmd = cmd

    def run(self):
        try:
            proc = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in proc.stdout:
                self.output.emit(line.rstrip())
            proc.wait()
        except Exception as e:
            self.output.emit(f"[ERROR] {e}")
        finally:
            self.finished.emit()


class NetworkToolsWidget(BaseModuleWidget):
    MODULE_TITLE = "🌐 Netzwerk Tools"
    MODULE_SUBTITLE = "Ping · Traceroute · DNS Lookup · Whois"

    def setup_ui(self):
        # Tool selector + input row
        row = QHBoxLayout()
        row.setSpacing(10)

        self.tool_combo = QComboBox()
        self.tool_combo.addItems(["Ping", "Traceroute", "DNS Lookup", "Reverse DNS", "Whois"])
        self.tool_combo.setFixedWidth(160)
        self.tool_combo.setStyleSheet(self.input_style())

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Hostname oder IP-Adresse...")
        self.target_input.setStyleSheet(self.input_style())
        self.target_input.returnPressed.connect(self._run)

        self.run_btn = QPushButton("▶  Ausführen")
        self.run_btn.setStyleSheet(self.button_style())
        self.run_btn.setFixedWidth(140)
        self.run_btn.clicked.connect(self._run)

        self.stop_btn = QPushButton("■  Stop")
        self.stop_btn.setStyleSheet(self.button_style(False))
        self.stop_btn.setFixedWidth(100)
        self.stop_btn.clicked.connect(self._stop)
        self.stop_btn.setEnabled(False)

        row.addWidget(self.tool_combo)
        row.addWidget(self.target_input)
        row.addWidget(self.run_btn)
        row.addWidget(self.stop_btn)
        self.content_layout.addLayout(row)

        # Quick DNS info card
        self.info_card = QFrame()
        self.info_card.setStyleSheet(self.card_style())
        info_layout = QHBoxLayout(self.info_card)
        info_layout.setContentsMargins(16, 12, 16, 12)

        self.hostname_label = QLabel(f"🖥️  Hostname: {socket.gethostname()}")
        self.hostname_label.setStyleSheet(self.label_style())
        self.hostname_label.setFont(QFont("Monospace", 9))

        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "N/A"
        self.localip_label = QLabel(f"📍 Lokale IP: {local_ip}")
        self.localip_label.setStyleSheet(self.label_style())
        self.localip_label.setFont(QFont("Monospace", 9))

        info_layout.addWidget(self.hostname_label)
        info_layout.addStretch()
        info_layout.addWidget(self.localip_label)
        self.content_layout.addWidget(self.info_card)

        # Output
        output_label = QLabel("Ausgabe:")
        output_label.setStyleSheet(self.label_style(muted=True))
        self.content_layout.addWidget(output_label)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(self.output_style())
        self.output.setFont(QFont("Monospace", 9))
        self.content_layout.addWidget(self.output)

        # Clear button
        clear_btn = QPushButton("🗑  Ausgabe leeren")
        clear_btn.setStyleSheet(self.button_style(False))
        clear_btn.setFixedWidth(180)
        clear_btn.clicked.connect(self.output.clear)
        self.content_layout.addWidget(clear_btn)

        self._thread = None

    def _run(self):
        target = self.target_input.text().strip()
        if not target:
            return

        tool = self.tool_combo.currentText()
        cmd = self._build_cmd(tool, target)
        if not cmd:
            return

        self.output.append(f"\n$ {' '.join(cmd)}\n{'─' * 50}")
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self._thread = CommandThread(cmd)
        self._thread.output.connect(lambda line: self.output.append(line))
        self._thread.finished.connect(self._done)
        self._thread.start()

    def _build_cmd(self, tool: str, target: str) -> list[str]:
        match tool:
            case "Ping":
                return ["ping", "-c", "4", target]
            case "Traceroute":
                return ["traceroute", target]
            case "DNS Lookup":
                return ["nslookup", target]
            case "Reverse DNS":
                return ["nslookup", target]
            case "Whois":
                return ["whois", target]
        return []

    def _stop(self):
        if self._thread and self._thread.isRunning():
            self._thread.terminate()
        self._done()

    def _done(self):
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.output.append("─" * 50 + "\n✅ Fertig\n")
