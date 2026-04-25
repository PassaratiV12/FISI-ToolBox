import random
import string
import re
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QSlider, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QClipboard
from PyQt6.QtWidgets import QApplication
from modules.base_widget import BaseModuleWidget


class PasswordGeneratorWidget(BaseModuleWidget):
    MODULE_TITLE = "🔑 Passwort Generator"
    MODULE_SUBTITLE = "Sicher · Anpassbar · Batch-Generierung"

    def setup_ui(self):
        # Length slider
        len_frame = QFrame()
        len_frame.setStyleSheet(self.card_style())
        len_layout = QVBoxLayout(len_frame)
        len_layout.setContentsMargins(16, 14, 16, 14)

        len_row = QHBoxLayout()
        len_label = QLabel("Länge:")
        len_label.setStyleSheet(self.label_style())
        len_label.setFont(QFont("Monospace", 10))
        self.len_value = QLabel("20")
        self.len_value.setStyleSheet("color: #00ff88; font-family: Monospace; font-size: 14pt; font-weight: bold;")
        self.len_value.setFixedWidth(50)
        len_row.addWidget(len_label)
        len_row.addWidget(self.len_value)
        len_row.addStretch()
        len_layout.addLayout(len_row)

        self.len_slider = QSlider(Qt.Orientation.Horizontal)
        self.len_slider.setRange(4, 128)
        self.len_slider.setValue(20)
        self.len_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #1a1a1a; height: 6px; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00ff88; width: 16px; height: 16px;
                margin: -5px 0; border-radius: 8px;
            }
            QSlider::sub-page:horizontal { background: #00ff88; border-radius: 3px; }
        """)
        self.len_slider.valueChanged.connect(lambda v: self.len_value.setText(str(v)))
        len_layout.addWidget(self.len_slider)
        self.content_layout.addWidget(len_frame)

        # Options
        opts_frame = QFrame()
        opts_frame.setStyleSheet(self.card_style())
        opts_layout = QHBoxLayout(opts_frame)
        opts_layout.setContentsMargins(16, 14, 16, 14)
        opts_layout.setSpacing(24)

        self.cb_upper = QCheckBox("Großbuchstaben (A-Z)")
        self.cb_lower = QCheckBox("Kleinbuchstaben (a-z)")
        self.cb_digits = QCheckBox("Zahlen (0-9)")
        self.cb_special = QCheckBox("Sonderzeichen (!@#...)")
        self.cb_exclude_ambiguous = QCheckBox("Mehrdeutige Zeichen ausschließen (0, O, l, 1)")

        for cb in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_special, self.cb_exclude_ambiguous]:
            cb.setChecked(True)
            cb.setStyleSheet("""
                QCheckBox { color: #a0a0a0; font-family: Monospace; font-size: 9pt; background: transparent; }
                QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #2a2a2a; border-radius: 3px; background: #1a1a1a; }
                QCheckBox::indicator:checked { background: #00ff88; border-color: #00ff88; }
            """)

        left = QVBoxLayout()
        left.addWidget(self.cb_upper)
        left.addWidget(self.cb_lower)
        right = QVBoxLayout()
        right.addWidget(self.cb_digits)
        right.addWidget(self.cb_special)
        opts_layout.addLayout(left)
        opts_layout.addLayout(right)
        opts_layout.addWidget(self.cb_exclude_ambiguous)
        self.content_layout.addWidget(opts_frame)

        # Count
        count_row = QHBoxLayout()
        count_label = QLabel("Anzahl generieren:")
        count_label.setStyleSheet(self.label_style())
        self.count_input = QLineEdit("1")
        self.count_input.setFixedWidth(80)
        self.count_input.setStyleSheet(self.input_style())
        count_row.addWidget(count_label)
        count_row.addWidget(self.count_input)
        count_row.addStretch()
        self.content_layout.addLayout(count_row)

        # Buttons
        btn_row = QHBoxLayout()
        gen_btn = QPushButton("⚡  Generieren")
        gen_btn.setStyleSheet(self.button_style())
        gen_btn.clicked.connect(self._generate)

        copy_btn = QPushButton("📋  Kopieren")
        copy_btn.setStyleSheet(self.button_style(False))
        copy_btn.clicked.connect(self._copy)

        clear_btn = QPushButton("🗑  Leeren")
        clear_btn.setStyleSheet(self.button_style(False))
        clear_btn.clicked.connect(self._clear)

        btn_row.addWidget(gen_btn)
        btn_row.addWidget(copy_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        self.content_layout.addLayout(btn_row)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(self.output_style())
        self.output.setFont(QFont("Monospace", 12))
        self.content_layout.addWidget(self.output)

        # Strength indicator
        self.strength_label = QLabel("")
        self.strength_label.setFont(QFont("Monospace", 9))
        self.content_layout.addWidget(self.strength_label)

    def _build_charset(self) -> str:
        charset = ""
        if self.cb_upper.isChecked():
            charset += string.ascii_uppercase
        if self.cb_lower.isChecked():
            charset += string.ascii_lowercase
        if self.cb_digits.isChecked():
            charset += string.digits
        if self.cb_special.isChecked():
            charset += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        if self.cb_exclude_ambiguous.isChecked():
            for c in "0O1lI":
                charset = charset.replace(c, "")
        return charset

    def _generate(self):
        charset = self._build_charset()
        if not charset:
            return
        length = self.len_slider.value()
        try:
            count = max(1, min(100, int(self.count_input.text())))
        except ValueError:
            count = 1

        passwords = []
        for _ in range(count):
            pw = "".join(random.choices(charset, k=length))
            passwords.append(pw)

        self.output.setPlainText("\n".join(passwords))
        if passwords:
            self._show_strength(passwords[0])

    def _show_strength(self, pw: str):
        score = 0
        if len(pw) >= 12: score += 1
        if len(pw) >= 20: score += 1
        if re.search(r"[A-Z]", pw): score += 1
        if re.search(r"[a-z]", pw): score += 1
        if re.search(r"\d", pw): score += 1
        if re.search(r"[^a-zA-Z\d]", pw): score += 1

        labels = ["Sehr schwach 🔴", "Schwach 🟠", "Mittel 🟡", "Gut 🟢", "Stark 🟢", "Sehr stark ✅"]
        colors = ["#ff4444", "#ff8800", "#ffcc00", "#88cc00", "#00cc44", "#00ff88"]
        idx = min(score, len(labels) - 1)
        self.strength_label.setText(f"Stärke: {labels[idx]}")
        self.strength_label.setStyleSheet(f"color: {colors[idx]}; font-family: Monospace;")

    def _copy(self):
        text = self.output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def _clear(self):
        self.output.clear()
        self.strength_label.clear()
