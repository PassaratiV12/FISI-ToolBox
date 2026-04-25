import ipaddress
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from modules.base_widget import BaseModuleWidget


class SubnetCalculatorWidget(BaseModuleWidget):
    MODULE_TITLE = "🧮 Subnetz Rechner"
    MODULE_SUBTITLE = "IPv4/IPv6 · CIDR · Netzwerkklassen"

    def setup_ui(self):
        # Input
        input_row = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP/CIDR, z.B. 192.168.1.0/24 oder 10.0.0.1/255.255.255.0")
        self.ip_input.setStyleSheet(self.input_style())
        self.ip_input.returnPressed.connect(self._calculate)

        calc_btn = QPushButton("🔢  Berechnen")
        calc_btn.setStyleSheet(self.button_style())
        calc_btn.setFixedWidth(150)
        calc_btn.clicked.connect(self._calculate)

        input_row.addWidget(self.ip_input)
        input_row.addWidget(calc_btn)
        self.content_layout.addLayout(input_row)

        # Quick examples
        ex_row = QHBoxLayout()
        ex_label = QLabel("Beispiele:")
        ex_label.setStyleSheet(self.label_style(muted=True))
        ex_row.addWidget(ex_label)
        for example in ["192.168.0.0/24", "10.0.0.0/8", "172.16.0.0/12", "192.168.1.100/26"]:
            btn = QPushButton(example)
            btn.setStyleSheet(self.button_style(False))
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda _, e=example: (self.ip_input.setText(e), self._calculate()))
            ex_row.addWidget(btn)
        ex_row.addStretch()
        self.content_layout.addLayout(ex_row)

        # Results grid
        self.results_frame = QFrame()
        self.results_frame.setStyleSheet(self.card_style())
        self.grid = QGridLayout(self.results_frame)
        self.grid.setContentsMargins(20, 16, 20, 16)
        self.grid.setSpacing(10)
        self.grid.setColumnStretch(1, 1)

        self._result_labels = {}
        fields = [
            ("Netzwerkadresse", "network"),
            ("Subnetzmaske", "netmask"),
            ("Wildcard Maske", "wildcard"),
            ("Broadcast", "broadcast"),
            ("Erste Host-IP", "first_host"),
            ("Letzte Host-IP", "last_host"),
            ("Anzahl Hosts", "num_hosts"),
            ("CIDR Notation", "cidr"),
            ("IP-Klasse", "ip_class"),
            ("Typ", "ip_type"),
        ]
        for i, (label, key) in enumerate(fields):
            lbl = QLabel(f"{label}:")
            lbl.setFont(QFont("Monospace", 9))
            lbl.setStyleSheet("color: #555; background: transparent; border: none;")
            val = QLabel("—")
            val.setFont(QFont("Monospace", 10, QFont.Weight.Bold))
            val.setStyleSheet("color: #e0e0e0; background: transparent; border: none;")
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.grid.addWidget(lbl, i, 0)
            self.grid.addWidget(val, i, 1)
            self._result_labels[key] = val

        self.content_layout.addWidget(self.results_frame)

        # Subnet split table
        split_label = QLabel("Subnetz Aufteilung (erste 16):")
        split_label.setStyleSheet(self.label_style(muted=True))
        self.content_layout.addWidget(split_label)

        self.subnet_table = QTableWidget(0, 4)
        self.subnet_table.setHorizontalHeaderLabels(["Netzwerk", "Erste IP", "Letzte IP", "Broadcast"])
        self.subnet_table.horizontalHeader().setStretchLastSection(True)
        self.subnet_table.setStyleSheet(self.table_style())
        self.subnet_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.subnet_table.setMaximumHeight(200)
        self.content_layout.addWidget(self.subnet_table)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff4444; font-family: Monospace;")
        self.content_layout.addWidget(self.error_label)

    def _calculate(self):
        text = self.ip_input.text().strip()
        self.error_label.clear()
        self.subnet_table.setRowCount(0)

        try:
            network = ipaddress.ip_network(text, strict=False)
        except ValueError as e:
            self.error_label.setText(f"❌ Ungültige Eingabe: {e}")
            return

        hosts = list(network.hosts())
        first_host = str(hosts[0]) if hosts else "N/A"
        last_host = str(hosts[-1]) if hosts else "N/A"
        num_hosts = len(hosts)

        # IP Class
        if isinstance(network, ipaddress.IPv4Network):
            first_octet = int(str(network.network_address).split(".")[0])
            if first_octet < 128:
                ip_class = "A"
            elif first_octet < 192:
                ip_class = "B"
            elif first_octet < 224:
                ip_class = "C"
            elif first_octet < 240:
                ip_class = "D (Multicast)"
            else:
                ip_class = "E (Reserviert)"
        else:
            ip_class = "IPv6"

        ip_type = "Privat" if network.is_private else ("Loopback" if network.is_loopback else "Öffentlich")

        self._result_labels["network"].setText(str(network.network_address))
        self._result_labels["netmask"].setText(str(network.netmask))
        self._result_labels["wildcard"].setText(str(network.hostmask))
        self._result_labels["broadcast"].setText(str(network.broadcast_address) if isinstance(network, ipaddress.IPv4Network) else "N/A")
        self._result_labels["first_host"].setText(first_host)
        self._result_labels["last_host"].setText(last_host)
        self._result_labels["num_hosts"].setText(f"{num_hosts:,}")
        self._result_labels["cidr"].setText(str(network))
        self._result_labels["ip_class"].setText(ip_class)
        self._result_labels["ip_type"].setText(ip_type)

        # Highlight network address green
        self._result_labels["network"].setStyleSheet("color: #00ff88; font-family: Monospace; font-size: 10pt; font-weight: bold; background: transparent; border: none;")
