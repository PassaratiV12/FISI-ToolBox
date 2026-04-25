import re
import subprocess
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QFrame,
    QFileDialog, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor
from modules.base_widget import BaseModuleWidget


LOG_SOURCES = [
    "Datei öffnen...",
    "journalctl (System)",
    "journalctl -xe (Fehler)",
    "journalctl -u NetworkManager",
    "journalctl -u sshd",
    "dmesg",
    "/var/log/dnf.log",
    "/var/log/messages",
    "/var/log/secure",
    "/var/log/auth.log",
    "/var/log/syslog",
]

HIGHLIGHT_RULES = [
    (r"(error|fehler|critical|crit|emerg)", QColor("#ff4444")),
    (r"(warning|warn|warnung)", QColor("#ffaa00")),
    (r"(info|notice)", QColor("#00aaff")),
    (r"(success|ok|started|active)", QColor("#00ff88")),
    (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", QColor("#aa88ff")),
]


class LogLoaderThread(QThread):
    lines_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, source: str, file_path: str = ""):
        super().__init__()
        self.source = source
        self.file_path = file_path

    def run(self):
        import os
        try:
            if self.source == "Datei öffnen..." and self.file_path:
                with open(self.file_path, "r", errors="replace") as f:
                    lines = f.readlines()
            elif self.source.startswith("journalctl"):
                cmd = self.source.split() + ["-n", "2000", "--no-pager"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                lines = result.stdout.splitlines(keepends=True)
                if not lines and result.stderr:
                    self.error.emit(result.stderr.strip())
                    return
            elif self.source == "dmesg":
                result = subprocess.run(["dmesg", "--human", "--color=never"], capture_output=True, text=True)
                lines = result.stdout.splitlines(keepends=True)
            else:
                if not os.path.exists(self.source):
                    self.error.emit(
                        f"Datei nicht gefunden: '{self.source}'\n"
                        "Tipp: Diese Log-Datei existiert nicht auf diesem System. "
                        "Nutze journalctl oder 'Datei oeffnen...'."
                    )
                    return
                with open(self.source, "r", errors="replace") as f:
                    lines = f.readlines()
            self.lines_ready.emit(lines)
        except PermissionError:
            self.error.emit(
                f"Zugriff verweigert auf '{self.source}'\n"
                "Tipp: Starte die App mit sudo fuer System-Logs."
            )
        except Exception as e:
            self.error.emit(str(e))


class LogFilterWidget(BaseModuleWidget):
    MODULE_TITLE = "📋 Log Filter"
    MODULE_SUBTITLE = "Syslog · journalctl · Datei-Logs · Regex-Filter"

    def setup_ui(self):
        self._all_lines: list[str] = []

        # Source row
        src_row = QHBoxLayout()
        src_row.setSpacing(10)

        self.source_combo = QComboBox()
        self.source_combo.addItems(LOG_SOURCES)
        self.source_combo.setStyleSheet(self.input_style())
        self.source_combo.setFixedWidth(240)

        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Pfad (bei Datei)...")
        self.file_path.setReadOnly(True)
        self.file_path.setStyleSheet(self.input_style())

        browse_btn = QPushButton("📂")
        browse_btn.setFixedWidth(40)
        browse_btn.setStyleSheet(self.button_style(False))
        browse_btn.clicked.connect(self._browse)

        load_btn = QPushButton("📥  Laden")
        load_btn.setStyleSheet(self.button_style())
        load_btn.setFixedWidth(110)
        load_btn.clicked.connect(self._load)

        src_row.addWidget(self.source_combo)
        src_row.addWidget(self.file_path)
        src_row.addWidget(browse_btn)
        src_row.addWidget(load_btn)
        self.content_layout.addLayout(src_row)

        # Filter row
        filter_frame = QFrame()
        filter_frame.setStyleSheet(self.card_style())
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(12)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter (Text oder Regex)...")
        self.filter_input.setStyleSheet(self.input_style())
        self.filter_input.textChanged.connect(self._apply_filter)

        self.cb_regex = QCheckBox("Regex")
        self.cb_case = QCheckBox("Groß-/Kleinschreibung")
        self.cb_errors = QCheckBox("Nur Fehler")
        self.cb_warn = QCheckBox("Nur Warnungen")

        for cb in [self.cb_regex, self.cb_case, self.cb_errors, self.cb_warn]:
            cb.setStyleSheet("""
                QCheckBox { color: #a0a0a0; font-family: Monospace; font-size: 9pt; background: transparent; }
                QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #2a2a2a; border-radius: 3px; background: #1a1a1a; }
                QCheckBox::indicator:checked { background: #00ff88; border-color: #00ff88; }
            """)
            cb.stateChanged.connect(self._apply_filter)

        filter_layout.addWidget(self.filter_input)
        filter_layout.addWidget(self.cb_regex)
        filter_layout.addWidget(self.cb_case)
        filter_layout.addWidget(self.cb_errors)
        filter_layout.addWidget(self.cb_warn)
        self.content_layout.addWidget(filter_frame)

        # Status
        self.status_label = QLabel("Keine Logs geladen.")
        self.status_label.setStyleSheet(self.label_style(muted=True))
        self.content_layout.addWidget(self.status_label)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(self.output_style())
        self.output.setFont(QFont("Monospace", 9))
        self.content_layout.addWidget(self.output)

        # Bottom buttons
        btn_row = QHBoxLayout()
        clear_btn = QPushButton("🗑  Leeren")
        clear_btn.setStyleSheet(self.button_style(False))
        clear_btn.clicked.connect(self.output.clear)
        save_btn = QPushButton("💾  Speichern")
        save_btn.setStyleSheet(self.button_style(False))
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(save_btn)
        btn_row.addStretch()
        self.content_layout.addLayout(btn_row)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Log-Datei öffnen")
        if path:
            self.file_path.setText(path)
            self.source_combo.setCurrentIndex(0)

    def _load(self):
        source = self.source_combo.currentText()
        file_path = self.file_path.text() if source == "Datei öffnen..." else ""
        if source == "Datei öffnen..." and not file_path:
            return
        self.status_label.setText("⏳ Lade Logs...")
        self._thread = LogLoaderThread(source, file_path)
        self._thread.lines_ready.connect(self._on_loaded)
        self._thread.error.connect(lambda e: self.status_label.setText(f"❌ Fehler: {e}"))
        self._thread.start()

    def _on_loaded(self, lines: list[str]):
        self._all_lines = lines
        self._apply_filter()
        self.status_label.setText(f"✅ {len(lines)} Zeilen geladen.")

    def _apply_filter(self):
        filter_text = self.filter_input.text()
        use_regex = self.cb_regex.isChecked()
        case_sens = self.cb_case.isChecked()
        only_err = self.cb_errors.isChecked()
        only_warn = self.cb_warn.isChecked()

        flags = 0 if case_sens else re.IGNORECASE

        filtered = []
        for line in self._all_lines:
            if only_err and not re.search(r"error|critical|crit|emerg", line, re.IGNORECASE):
                continue
            if only_warn and not re.search(r"warning|warn", line, re.IGNORECASE):
                continue
            if filter_text:
                try:
                    pattern = filter_text if use_regex else re.escape(filter_text)
                    if not re.search(pattern, line, flags):
                        continue
                except re.error:
                    if filter_text.lower() not in line.lower():
                        continue
            filtered.append(line)

        self.output.setPlainText("".join(filtered))
        self.status_label.setText(f"📊 {len(filtered)} / {len(self._all_lines)} Zeilen angezeigt.")
        self._highlight()

    def _highlight(self):
        doc = self.output.document()
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        for pattern, color in HIGHLIGHT_RULES:
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            regex = re.compile(pattern, re.IGNORECASE)
            full_text = self.output.toPlainText()
            for match in regex.finditer(full_text):
                c = QTextCursor(doc)
                c.setPosition(match.start())
                c.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
                c.setCharFormat(fmt)

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Log speichern", filter="Text (*.txt);;Log (*.log)")
        if path:
            with open(path, "w") as f:
                f.write(self.output.toPlainText())
