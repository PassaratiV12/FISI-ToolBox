import socket
import threading
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from modules.base_widget import BaseModuleWidget


COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB",
}


class ScanThread(QThread):
    found = pyqtSignal(int, str, bool)   # port, service, open
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, host: str, start_port: int, end_port: int, timeout: float = 0.5):
        super().__init__()
        self.host = host
        self.start_port = start_port
        self.end_port = end_port
        self.timeout = timeout
        self._running = True

    def run(self):
        total = self.end_port - self.start_port + 1
        lock = threading.Lock()
        scanned = [0]

        def scan_port(port):
            if not self._running:
                return
            service = COMMON_PORTS.get(port, "Unknown")
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(self.timeout)
                result = s.connect_ex((self.host, port))
                s.close()
                is_open = result == 0
            except Exception:
                is_open = False

            self.found.emit(port, service, is_open)
            with lock:
                scanned[0] += 1
                pct = int(scanned[0] / total * 100)
                self.progress.emit(pct)

        threads = []
        for port in range(self.start_port, self.end_port + 1):
            t = threading.Thread(target=scan_port, args=(port,), daemon=True)
            threads.append(t)
            t.start()
            if len(threads) >= 100:
                for t in threads:
                    t.join()
                threads.clear()

        for t in threads:
            t.join()
        self.finished.emit()

    def stop(self):
        self._running = False


class PortScannerWidget(BaseModuleWidget):
    MODULE_TITLE = "🔍 Port Scanner"
    MODULE_SUBTITLE = "TCP Port-Scan mit Service-Erkennung"

    def setup_ui(self):
        # Input row
        row = QHBoxLayout()
        row.setSpacing(10)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Host oder IP...")
        self.host_input.setStyleSheet(self.input_style())

        lbl_from = QLabel("Von:")
        lbl_from.setStyleSheet(self.label_style())

        self.port_from = QSpinBox()
        self.port_from.setRange(1, 65535)
        self.port_from.setValue(1)
        self.port_from.setFixedWidth(90)
        self.port_from.setStyleSheet(self.input_style())

        lbl_to = QLabel("Bis:")
        lbl_to.setStyleSheet(self.label_style())

        self.port_to = QSpinBox()
        self.port_to.setRange(1, 65535)
        self.port_to.setValue(1024)
        self.port_to.setFixedWidth(90)
        self.port_to.setStyleSheet(self.input_style())

        self.scan_btn = QPushButton("▶  Scan starten")
        self.scan_btn.setStyleSheet(self.button_style())
        self.scan_btn.setFixedWidth(150)
        self.scan_btn.clicked.connect(self._start_scan)

        self.stop_btn = QPushButton("■  Stop")
        self.stop_btn.setStyleSheet(self.button_style(False))
        self.stop_btn.setFixedWidth(90)
        self.stop_btn.clicked.connect(self._stop_scan)
        self.stop_btn.setEnabled(False)

        row.addWidget(self.host_input)
        row.addWidget(lbl_from)
        row.addWidget(self.port_from)
        row.addWidget(lbl_to)
        row.addWidget(self.port_to)
        row.addWidget(self.scan_btn)
        row.addWidget(self.stop_btn)
        self.content_layout.addLayout(row)

        # Quick presets
        presets_row = QHBoxLayout()
        presets_row.setSpacing(8)
        presets_label = QLabel("Schnell-Scan:")
        presets_label.setStyleSheet(self.label_style(muted=True))
        presets_row.addWidget(presets_label)

        presets = [("Top 20", 1, 1024), ("Web", 80, 443), ("DB", 3306, 5432), ("Full", 1, 65535)]
        for name, s, e in presets:
            btn = QPushButton(name)
            btn.setStyleSheet(self.button_style(False))
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda _, s=s, e=e: (
                self.port_from.setValue(s),
                self.port_to.setValue(e)
            ))
            presets_row.addWidget(btn)
        presets_row.addStretch()
        self.content_layout.addLayout(presets_row)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: #555;
            }
            QProgressBar::chunk {
                background: #00ff88;
                border-radius: 4px;
            }
        """)
        self.progress.setValue(0)
        self.content_layout.addWidget(self.progress)

        # Status
        self.status_label = QLabel("Bereit.")
        self.status_label.setStyleSheet(self.label_style(muted=True))
        self.content_layout.addWidget(self.status_label)

        # Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Port", "Service", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 200)
        self.table.setStyleSheet(self.table_style())
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.content_layout.addWidget(self.table)

        self._thread = None

    def _start_scan(self):
        host = self.host_input.text().strip()
        if not host:
            return

        self.table.setRowCount(0)
        self.progress.setValue(0)
        self.status_label.setText(f"Scanne {host}...")
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self._thread = ScanThread(host, self.port_from.value(), self.port_to.value())
        self._thread.found.connect(self._add_result)
        self._thread.progress.connect(self.progress.setValue)
        self._thread.finished.connect(self._scan_done)
        self._thread.start()

    def _add_result(self, port: int, service: str, is_open: bool):
        if not is_open:
            return
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(port)))
        self.table.setItem(row, 1, QTableWidgetItem(service))
        status = QTableWidgetItem("✅ OPEN")
        status.setForeground(QColor("#00ff88"))
        self.table.setItem(row, 2, status)

    def _stop_scan(self):
        if self._thread:
            self._thread.stop()
        self._scan_done()

    def _scan_done(self):
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        open_count = self.table.rowCount()
        self.status_label.setText(f"✅ Scan abgeschlossen — {open_count} offene Ports gefunden.")
