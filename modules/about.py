from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from modules.base_widget import BaseModuleWidget
import os


class AboutWidget(BaseModuleWidget):
    MODULE_TITLE = "ℹ️  About & Imprint"
    MODULE_SUBTITLE = "Legal Information · Credits · License"

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # App icon + name
        header_frame = QFrame()
        header_frame.setStyleSheet(self.card_style())
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(24)

        icon_lbl = QLabel()
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_lbl.setPixmap(pix)
        else:
            icon_lbl.setText("⚡")
            icon_lbl.setFont(QFont("Monospace", 48))
        icon_lbl.setStyleSheet("background: transparent; border: none;")

        name_layout = QVBoxLayout()
        app_name = QLabel("FISI Toolbox")
        app_name.setFont(QFont("Monospace", 24, QFont.Weight.Bold))
        app_name.setStyleSheet("color: #00ff88; background: transparent; border: none;")
        app_version = QLabel("Version 1.0.0")
        app_version.setFont(QFont("Monospace", 10))
        app_version.setStyleSheet("color: #555; background: transparent; border: none;")
        app_desc = QLabel("All-in-one IT toolbox for FISI professionals.\nBuilt for Fedora · Debian · Ubuntu.")
        app_desc.setFont(QFont("Monospace", 10))
        app_desc.setStyleSheet("color: #a0a0a0; background: transparent; border: none;")
        app_desc.setWordWrap(True)
        name_layout.addWidget(app_name)
        name_layout.addWidget(app_version)
        name_layout.addSpacing(8)
        name_layout.addWidget(app_desc)

        header_layout.addWidget(icon_lbl)
        header_layout.addLayout(name_layout)
        header_layout.addStretch()
        layout.addWidget(header_frame)

        # Imprint
        imprint_frame = QFrame()
        imprint_frame.setStyleSheet(self.card_style())
        imprint_layout = QVBoxLayout(imprint_frame)
        imprint_layout.setContentsMargins(24, 20, 24, 20)
        imprint_layout.setSpacing(16)

        self._section_title(imprint_layout, "📋  Imprint")

        imprint_data = [
            ("Developer",       "Cedric Thieme"),
            ("Role",            "IT Specialist for System Integration (FISI)"),
            ("Application",     "FISI Toolbox"),
            ("Purpose",         "Internal IT toolbox for daily operational tasks"),
            ("Target Platform", "Linux (Fedora, Debian, Ubuntu and derivatives)"),
            ("Distribution",    "Internal use · Flatpak"),
            ("Contact",         "Cedric Thieme"),
        ]
        for label, value in imprint_data:
            self._info_row(imprint_layout, label, value)

        layout.addWidget(imprint_frame)

        # Features
        features_frame = QFrame()
        features_frame.setStyleSheet(self.card_style())
        features_layout = QVBoxLayout(features_frame)
        features_layout.setContentsMargins(24, 20, 24, 20)
        features_layout.setSpacing(8)

        self._section_title(features_layout, "📦  Included Modules")

        modules = [
            ("🌐", "Network Tools",         "Ping, Traceroute, DNS Lookup, Whois"),
            ("🔍", "Port Scanner",           "TCP port scanning with service detection"),
            ("📡", "Ping Monitor",           "Continuous ping with live graph"),
            ("🖥️",  "System Info",            "CPU, RAM, Disk, Uptime — auto-refreshing"),
            ("⚙️",  "Process Manager",        "View and terminate running processes"),
            ("🔑", "Password Generator",     "Configurable secure password generation"),
            ("#",  "Hash Generator",         "MD5, SHA1, SHA256, SHA512, BLAKE2b"),
            ("📋", "Log Filter",             "journalctl, syslog, regex filtering"),
            ("🧮", "Subnet Calculator",      "IPv4/IPv6 CIDR network calculation"),
            ("💡", "Wake-on-LAN",            "Send magic packets to wake devices"),
            ("🔒", "SSL Certificate Checker","Expiry, issuer, cipher, SAN"),
            ("⏰", "Cron Builder",           "Build and explain cron expressions"),
            ("📝", "Notes & Snippets",       "Local knowledge base, persisted on disk"),
        ]
        for icon, name, desc in modules:
            row = QHBoxLayout()
            icon_l = QLabel(icon)
            icon_l.setFixedWidth(24)
            icon_l.setStyleSheet("background: transparent; border: none;")
            name_l = QLabel(name)
            name_l.setFont(QFont("Monospace", 9, QFont.Weight.Bold))
            name_l.setFixedWidth(200)
            name_l.setStyleSheet("color: #00ff88; background: transparent; border: none;")
            desc_l = QLabel(desc)
            desc_l.setFont(QFont("Monospace", 9))
            desc_l.setStyleSheet("color: #666; background: transparent; border: none;")
            row.addWidget(icon_l)
            row.addWidget(name_l)
            row.addWidget(desc_l)
            row.addStretch()
            features_layout.addLayout(row)

        layout.addWidget(features_frame)

        layout.addStretch()
        scroll.setWidget(container)
        self.content_layout.addWidget(scroll)

    def _section_title(self, layout, text: str):
        lbl = QLabel(text)
        lbl.setFont(QFont("Monospace", 11, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #00ff88; background: transparent; border: none; padding-bottom: 4px;")
        layout.addWidget(lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #1e1e1e; background: #1e1e1e; border: none;")
        line.setFixedHeight(1)
        layout.addWidget(line)

    def _info_row(self, layout, label: str, value: str):
        row = QHBoxLayout()
        lbl = QLabel(f"{label}:")
        lbl.setFont(QFont("Monospace", 9))
        lbl.setStyleSheet("color: #555; background: transparent; border: none;")
        lbl.setFixedWidth(160)
        val = QLabel(value)
        val.setFont(QFont("Monospace", 9, QFont.Weight.Bold))
        val.setStyleSheet("color: #e0e0e0; background: transparent; border: none;")
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row.addWidget(lbl)
        row.addWidget(val)
        row.addStretch()
        layout.addLayout(row)
