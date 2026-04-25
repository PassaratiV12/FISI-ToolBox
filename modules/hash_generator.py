import hashlib
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QFrame,
    QFileDialog, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication
from modules.base_widget import BaseModuleWidget

ALGORITHMS = ["MD5", "SHA1", "SHA256", "SHA384", "SHA512", "SHA3-256", "BLAKE2b"]


class HashGeneratorWidget(BaseModuleWidget):
    MODULE_TITLE = "Hash Generator"
    MODULE_SUBTITLE = "MD5 · SHA1 · SHA256 · SHA512 · Datei-Hashing"

    def setup_ui(self):
        # Text input section
        text_frame = QFrame()
        text_frame.setStyleSheet(self.card_style())
        text_layout = QVBoxLayout(text_frame)
        text_layout.setContentsMargins(16, 14, 16, 14)
        text_layout.setSpacing(10)

        lbl = QLabel("Text / Eingabe:")
        lbl.setStyleSheet(self.label_style())
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Text hier eingeben...")
        self.text_input.setStyleSheet(self.input_style())
        self.text_input.setMaximumHeight(100)
        self.text_input.textChanged.connect(self._hash_text)

        text_layout.addWidget(lbl)
        text_layout.addWidget(self.text_input)
        self.content_layout.addWidget(text_frame)

        # File section
        file_row = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Datei auswählen...")
        self.file_path.setReadOnly(True)
        self.file_path.setStyleSheet(self.input_style())

        browse_btn = QPushButton("📂  Datei wählen")
        browse_btn.setStyleSheet(self.button_style(False))
        browse_btn.clicked.connect(self._browse_file)

        hash_file_btn = QPushButton("🔐  Datei hashen")
        hash_file_btn.setStyleSheet(self.button_style())
        hash_file_btn.clicked.connect(self._hash_file)

        file_row.addWidget(self.file_path)
        file_row.addWidget(browse_btn)
        file_row.addWidget(hash_file_btn)
        self.content_layout.addLayout(file_row)

        # Hash results grid
        results_frame = QFrame()
        results_frame.setStyleSheet(self.card_style())
        grid = QGridLayout(results_frame)
        grid.setContentsMargins(16, 14, 16, 14)
        grid.setSpacing(10)

        self._hash_fields = {}
        for i, algo in enumerate(ALGORITHMS):
            lbl = QLabel(f"{algo}:")
            lbl.setFont(QFont("Monospace", 9, QFont.Weight.Bold))
            lbl.setStyleSheet("color: #00ff88; background: transparent; border: none;")
            lbl.setFixedWidth(90)

            val = QLineEdit()
            val.setReadOnly(True)
            val.setStyleSheet(self.input_style())
            val.setFont(QFont("Monospace", 9))

            copy_btn = QPushButton("📋")
            copy_btn.setFixedWidth(36)
            copy_btn.setFixedHeight(34)
            copy_btn.setStyleSheet(self.button_style(False))
            copy_btn.clicked.connect(lambda _, f=val: QApplication.clipboard().setText(f.text()))

            grid.addWidget(lbl, i, 0)
            grid.addWidget(val, i, 1)
            grid.addWidget(copy_btn, i, 2)
            self._hash_fields[algo] = val

        self.content_layout.addWidget(results_frame)

        # Verify section
        verify_frame = QFrame()
        verify_frame.setStyleSheet(self.card_style())
        v_layout = QVBoxLayout(verify_frame)
        v_layout.setContentsMargins(16, 12, 16, 12)
        v_layout.setSpacing(8)

        v_lbl = QLabel("Hash verifizieren:")
        v_lbl.setStyleSheet(self.label_style())
        v_row = QHBoxLayout()
        self.verify_input = QLineEdit()
        self.verify_input.setPlaceholderText("Hash zum Vergleichen eingeben...")
        self.verify_input.setStyleSheet(self.input_style())
        verify_btn = QPushButton("✓ Prüfen")
        verify_btn.setStyleSheet(self.button_style())
        verify_btn.clicked.connect(self._verify)
        self.verify_result = QLabel("")
        self.verify_result.setFont(QFont("Monospace", 10))

        v_row.addWidget(self.verify_input)
        v_row.addWidget(verify_btn)
        v_layout.addWidget(v_lbl)
        v_layout.addLayout(v_row)
        v_layout.addWidget(self.verify_result)
        self.content_layout.addWidget(verify_frame)

    def _compute_hashes(self, data: bytes):
        mapping = {
            "MD5": hashlib.md5,
            "SHA1": hashlib.sha1,
            "SHA256": hashlib.sha256,
            "SHA384": hashlib.sha384,
            "SHA512": hashlib.sha512,
            "SHA3-256": hashlib.sha3_256,
            "BLAKE2b": hashlib.blake2b,
        }
        for algo, fn in mapping.items():
            self._hash_fields[algo].setText(fn(data).hexdigest())

    def _hash_text(self):
        text = self.text_input.toPlainText()
        if text:
            self._compute_hashes(text.encode("utf-8"))
        else:
            for f in self._hash_fields.values():
                f.clear()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Datei auswählen")
        if path:
            self.file_path.setText(path)

    def _hash_file(self):
        path = self.file_path.text()
        if not path:
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
            self._compute_hashes(data)
        except Exception as e:
            for field in self._hash_fields.values():
                field.setText(f"Fehler: {e}")

    def _verify(self):
        check = self.verify_input.text().strip().lower()
        for algo, field in self._hash_fields.items():
            if field.text().lower() == check:
                self.verify_result.setText(f"✅ Übereinstimmung: {algo}")
                self.verify_result.setStyleSheet("color: #00ff88; font-family: Monospace;")
                return
        self.verify_result.setText("❌ Kein Treffer — Hash stimmt nicht überein.")
        self.verify_result.setStyleSheet("color: #ff4444; font-family: Monospace;")
