import platform
import psutil
import socket
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QFrame,
    QPushButton, QGridLayout, QProgressBar, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from modules.base_widget import BaseModuleWidget


class StatCard(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #111111;
                border: 1px solid #1e1e1e;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Monospace", 8))
        self.title_lbl.setStyleSheet("color: #555; background: transparent; border: none;")

        self.value_lbl = QLabel("—")
        self.value_lbl.setFont(QFont("Monospace", 20, QFont.Weight.Bold))
        self.value_lbl.setStyleSheet("color: #00ff88; background: transparent; border: none;")

        self.sub_lbl = QLabel("")
        self.sub_lbl.setFont(QFont("Monospace", 8))
        self.sub_lbl.setStyleSheet("color: #444; background: transparent; border: none;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)
        layout.addWidget(self.sub_lbl)

    def set_value(self, val: str, sub: str = ""):
        self.value_lbl.setText(val)
        self.sub_lbl.setText(sub)


class SystemInfoWidget(BaseModuleWidget):
    MODULE_TITLE = "🖥️  Systeminfo"
    MODULE_SUBTITLE = "CPU · RAM · Disk · Netzwerk · Uptime"

    def setup_ui(self):
        refresh_btn = QPushButton("🔄  Aktualisieren")
        refresh_btn.setStyleSheet(self.button_style(False))
        refresh_btn.setFixedWidth(180)
        refresh_btn.clicked.connect(self._refresh)
        self.content_layout.addWidget(refresh_btn)

        # Top stat cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.cpu_card = StatCard("CPU Auslastung")
        self.ram_card = StatCard("RAM Nutzung")
        self.disk_card = StatCard("Disk C:")
        self.uptime_card = StatCard("Uptime")
        for card in [self.cpu_card, self.ram_card, self.disk_card, self.uptime_card]:
            cards_row.addWidget(card)
        self.content_layout.addLayout(cards_row)

        # Progress bars
        bars_frame = QFrame()
        bars_frame.setStyleSheet(self.card_style())
        bars_layout = QVBoxLayout(bars_frame)
        bars_layout.setContentsMargins(16, 14, 16, 14)
        bars_layout.setSpacing(12)

        self.cpu_bar = self._make_bar("CPU", bars_layout)
        self.ram_bar = self._make_bar("RAM", bars_layout)
        self.disk_bar = self._make_bar("Disk", bars_layout)
        self.content_layout.addWidget(bars_frame)

        # System info grid
        info_frame = QFrame()
        info_frame.setStyleSheet(self.card_style())
        grid = QGridLayout(info_frame)
        grid.setContentsMargins(16, 14, 16, 14)
        grid.setSpacing(8)

        self._info_labels = {}
        fields = [
            ("Betriebssystem", "os"),
            ("Kernel", "kernel"),
            ("Hostname", "hostname"),
            ("Lokale IP", "local_ip"),
            ("CPU Modell", "cpu_model"),
            ("CPU Kerne", "cpu_cores"),
            ("RAM Gesamt", "ram_total"),
            ("Python Version", "python"),
        ]
        for i, (label, key) in enumerate(fields):
            lbl = QLabel(f"{label}:")
            lbl.setFont(QFont("Monospace", 9))
            lbl.setStyleSheet("color: #555; background: transparent; border: none;")
            val = QLabel("—")
            val.setFont(QFont("Monospace", 9))
            val.setStyleSheet("color: #e0e0e0; background: transparent; border: none;")
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(lbl, i, 0)
            grid.addWidget(val, i, 1)
            self._info_labels[key] = val

        self.content_layout.addWidget(info_frame)

        # Auto-refresh every 3s
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh)
        self._timer.start(3000)
        self._refresh()

    def _make_bar(self, label: str, layout: QVBoxLayout):
        row = QHBoxLayout()
        lbl = QLabel(f"{label}:")
        lbl.setFont(QFont("Monospace", 9))
        lbl.setStyleSheet("color: #a0a0a0; background: transparent; border: none;")
        lbl.setFixedWidth(50)
        bar = QProgressBar()
        bar.setStyleSheet("""
            QProgressBar {
                background: #1a1a1a; border: 1px solid #2a2a2a;
                border-radius: 4px; height: 16px; color: transparent;
            }
            QProgressBar::chunk { background: #00ff88; border-radius: 4px; }
        """)
        pct_lbl = QLabel("0%")
        pct_lbl.setFont(QFont("Monospace", 9))
        pct_lbl.setStyleSheet("color: #00ff88; background: transparent; border: none;")
        pct_lbl.setFixedWidth(45)
        row.addWidget(lbl)
        row.addWidget(bar)
        row.addWidget(pct_lbl)
        layout.addLayout(row)
        return bar, pct_lbl

    def _refresh(self):
        cpu_pct = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        boot = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot
        uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))

        self.cpu_card.set_value(f"{cpu_pct:.0f}%", f"{psutil.cpu_count()} Kerne")
        self.ram_card.set_value(
            f"{ram.percent:.0f}%",
            f"{ram.used // 1024**3} / {ram.total // 1024**3} GB"
        )
        self.disk_card.set_value(
            f"{disk.percent:.0f}%",
            f"{disk.used // 1024**3} / {disk.total // 1024**3} GB"
        )
        self.uptime_card.set_value(uptime_str.split(":")[0] + "h", uptime_str)

        self.cpu_bar[0].setValue(int(cpu_pct))
        self.cpu_bar[1].setText(f"{cpu_pct:.0f}%")
        self.ram_bar[0].setValue(int(ram.percent))
        self.ram_bar[1].setText(f"{ram.percent:.0f}%")
        self.disk_bar[0].setValue(int(disk.percent))
        self.disk_bar[1].setText(f"{disk.percent:.0f}%")

        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "N/A"

        self._info_labels["os"].setText(f"{platform.system()} {platform.version()[:40]}")
        self._info_labels["kernel"].setText(platform.release())
        self._info_labels["hostname"].setText(socket.gethostname())
        self._info_labels["local_ip"].setText(local_ip)
        self._info_labels["cpu_model"].setText(platform.processor() or "N/A")
        self._info_labels["cpu_cores"].setText(f"{psutil.cpu_count(logical=False)} physisch / {psutil.cpu_count()} logisch")
        self._info_labels["ram_total"].setText(f"{ram.total // 1024**3} GB")
        self._info_labels["python"].setText(platform.python_version())
