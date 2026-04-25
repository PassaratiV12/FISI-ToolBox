import psutil
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from modules.base_widget import BaseModuleWidget


class ProcessManagerWidget(BaseModuleWidget):
    MODULE_TITLE = "⚙️  Prozess Manager"
    MODULE_SUBTITLE = "Laufende Prozesse · CPU/RAM · Kill"

    def setup_ui(self):
        # Controls row
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Prozess suchen...")
        self.search_input.setStyleSheet(self.input_style())
        self.search_input.textChanged.connect(self._apply_filter)

        self.refresh_btn = QPushButton("🔄  Aktualisieren")
        self.refresh_btn.setStyleSheet(self.button_style(False))
        self.refresh_btn.clicked.connect(self._refresh)

        self.kill_btn = QPushButton("🔴  Prozess beenden")
        self.kill_btn.setStyleSheet(self.button_style(False))
        self.kill_btn.clicked.connect(self._kill_process)

        self.auto_label = QLabel("Auto-Refresh: 5s")
        self.auto_label.setStyleSheet(self.label_style(muted=True))

        ctrl_row.addWidget(self.search_input)
        ctrl_row.addWidget(self.refresh_btn)
        ctrl_row.addWidget(self.kill_btn)
        ctrl_row.addWidget(self.auto_label)
        self.content_layout.addLayout(ctrl_row)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(self.label_style(muted=True))
        self.content_layout.addWidget(self.status_label)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["PID", "Name", "Status", "CPU %", "RAM MB", "User"])
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 90)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(self.table_style())
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        self.content_layout.addWidget(self.table)

        self._all_procs = []

        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh)
        self._timer.start(5000)
        self._refresh()

    def _refresh(self):
        self._all_procs = []
        for proc in psutil.process_iter(["pid", "name", "status", "cpu_percent", "memory_info", "username"]):
            try:
                self._all_procs.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        self.status_label.setText(f"📊 {len(self._all_procs)} Prozesse")
        self._apply_filter()

    def _apply_filter(self):
        query = self.search_input.text().lower()
        filtered = [p for p in self._all_procs if query in (p.get("name") or "").lower()] if query else self._all_procs

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(filtered))
        for row, proc in enumerate(filtered):
            pid = str(proc.get("pid", ""))
            name = proc.get("name", "")
            status = proc.get("status", "")
            cpu = f"{proc.get('cpu_percent', 0):.1f}"
            mem_info = proc.get("memory_info")
            mem = f"{mem_info.rss / 1024**2:.1f}" if mem_info else "0"
            user = proc.get("username") or ""

            for col, val in enumerate([pid, name, status, cpu, mem, user]):
                item = QTableWidgetItem(val)
                item.setFont(QFont("Monospace", 9))
                if col == 3 and float(cpu) > 20:
                    item.setForeground(QColor("#ff8800"))
                elif col == 2 and status == "running":
                    item.setForeground(QColor("#00ff88"))
                self.table.setItem(row, col, item)

        self.table.setSortingEnabled(True)

    def _kill_process(self):
        row = self.table.currentRow()
        if row < 0:
            return
        pid_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)
        if not pid_item:
            return

        pid = int(pid_item.text())
        name = name_item.text() if name_item else str(pid)

        reply = QMessageBox.question(
            self,
            "Prozess beenden",
            f"Prozess '{name}' (PID {pid}) wirklich beenden?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                self.status_label.setText(f"✅ Prozess {name} (PID {pid}) beendet.")
                self._refresh()
            except Exception as e:
                self.status_label.setText(f"❌ Fehler: {e}")
