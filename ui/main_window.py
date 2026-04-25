import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap

from modules.network_tools import NetworkToolsWidget
from modules.password_generator import PasswordGeneratorWidget
from modules.log_filter import LogFilterWidget
from modules.system_info import SystemInfoWidget
from modules.subnet_calculator import SubnetCalculatorWidget
from modules.hash_generator import HashGeneratorWidget
from modules.port_scanner import PortScannerWidget
from modules.ping_monitor import PingMonitorWidget
from modules.process_manager import ProcessManagerWidget
from modules.notes import NotesWidget
from modules.wake_on_lan import WakeOnLanWidget
from modules.ssl_checker import SSLCheckerWidget
from modules.cron_builder import CronBuilderWidget
from modules.about import AboutWidget


NAV_ITEMS = [
    ("", "Netzwerk",          "network"),
    ("", "Port Scanner",      "portscan"),
    ("", "Ping Monitor",      "ping"),
    ("",  "Systeminfo",       "sysinfo"),
    ("",  "Prozesse",         "processes"),
    ("", "Passwort Gen.",     "password"),
    ("",  "Hash Gen.",         "hash"),
    ("", "Log Filter",        "logs"),
    ("", "Subnetz Rechner",   "subnet"),
    ("", "Wake-on-LAN",       "wol"),
    ("", "SSL Checker",       "ssl"),
    ("", "Cron Builder",      "cron"),
    ("", "Notizen",           "notes"),
    ("",  "About & Imprint",  "about"),
]


class SidebarButton(QPushButton):
    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(46)
        self.setText(f"  {icon_text}  {label}")
        self.setFont(QFont("Monospace", 10))
        self._apply_style(False)

    def _apply_style(self, active: bool):
        if active:
            self.setStyleSheet("""
                QPushButton {
                    background: #00ff88;
                    color: #0a0a0a;
                    border: none;
                    border-radius: 6px;
                    text-align: left;
                    padding-left: 16px;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #a0a0a0;
                    border: none;
                    border-radius: 6px;
                    text-align: left;
                    padding-left: 16px;
                }
                QPushButton:hover {
                    background: #1e1e1e;
                    color: #ffffff;
                }
            """)

    def setActive(self, active: bool):
        self._apply_style(active)
        self.setChecked(active)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FISI Toolbox")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 820)

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._build_ui()
        self._nav_buttons[0].setActive(True)

    def _build_ui(self):
        root = QWidget()
        root.setStyleSheet("background: #0d0d0d;")
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())

        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background: #1e1e1e;")
        layout.addWidget(divider)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: #0d0d0d;")
        self._populate_stack()
        layout.addWidget(self._stack)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background: #111111;")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(2)

        # Icon + title header
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        icon_lbl = QLabel()
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_lbl.setPixmap(pix)
        else:
            icon_lbl.setText("⚡")
            icon_lbl.setFont(QFont("Monospace", 22))
        icon_lbl.setStyleSheet("background: transparent;")

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title_lbl = QLabel("FISI Toolbox")
        title_lbl.setFont(QFont("Monospace", 11, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #00ff88; background: transparent;")
        ver_lbl = QLabel("v1.0.0  ·  by Cedric Thieme")
        ver_lbl.setFont(QFont("Monospace", 7))
        ver_lbl.setStyleSheet("color: #333; background: transparent;")
        title_col.addWidget(title_lbl)
        title_col.addWidget(ver_lbl)

        header_row.addWidget(icon_lbl)
        header_row.addLayout(title_col)
        layout.addLayout(header_row)
        layout.addSpacing(14)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: #1e1e1e; background: #1e1e1e;")
        div.setFixedHeight(1)
        layout.addWidget(div)
        layout.addSpacing(8)

        self._nav_buttons: list[SidebarButton] = []
        for i, (icon, label, _key) in enumerate(NAV_ITEMS):
            if label == "About & Imprint":
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("color: #1e1e1e; background: #1e1e1e;")
                sep.setFixedHeight(1)
                layout.addSpacing(6)
                layout.addWidget(sep)
                layout.addSpacing(6)

            btn = SidebarButton(icon, label)
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        footer = QLabel("Fedora · Debian · Ubuntu")
        footer.setFont(QFont("Monospace", 7))
        footer.setStyleSheet("color: #2a2a2a; padding: 4px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        return sidebar

    def _populate_stack(self):
        widgets = [
            NetworkToolsWidget(),
            PortScannerWidget(),
            PingMonitorWidget(),
            SystemInfoWidget(),
            ProcessManagerWidget(),
            PasswordGeneratorWidget(),
            HashGeneratorWidget(),
            LogFilterWidget(),
            SubnetCalculatorWidget(),
            WakeOnLanWidget(),
            SSLCheckerWidget(),
            CronBuilderWidget(),
            NotesWidget(),
            AboutWidget(),
        ]
        for w in widgets:
            self._stack.addWidget(w)

    def _switch_tab(self, index: int):
        for i, btn in enumerate(self._nav_buttons):
            btn.setActive(i == index)
        self._stack.setCurrentIndex(index)
