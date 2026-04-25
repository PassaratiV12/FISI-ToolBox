import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QListWidget, QListWidgetItem,
    QFrame, QSplitter, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from modules.base_widget import BaseModuleWidget

NOTES_FILE = os.path.expanduser("~/.fisi_toolbox_notes.json")


class NotesWidget(BaseModuleWidget):
    MODULE_TITLE = "📝 Notizen & Snippets"
    MODULE_SUBTITLE = "Lokale Wissensdatenbank · Commands · Configs"

    def setup_ui(self):
        self._notes: dict[str, dict] = {}
        self._current_key: str | None = None

        # Splitter: left = list, right = editor
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: #1e1e1e; }")

        # Left panel
        left = QFrame()
        left.setStyleSheet("background: #111111; border: 1px solid #1e1e1e; border-radius: 8px;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        left_header = QLabel("Notizen")
        left_header.setFont(QFont("Monospace", 10, QFont.Weight.Bold))
        left_header.setStyleSheet("color: #00ff88; background: transparent; border: none;")
        left_layout.addWidget(left_header)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suchen...")
        self.search_input.setStyleSheet(self.input_style())
        self.search_input.textChanged.connect(self._filter_list)
        left_layout.addWidget(self.search_input)

        self.note_list = QListWidget()
        self.note_list.setStyleSheet("""
            QListWidget {
                background: transparent; border: none;
                font-family: Monospace; font-size: 9pt; color: #a0a0a0;
            }
            QListWidget::item:selected { background: #00ff8820; color: #00ff88; border-radius: 4px; }
            QListWidget::item:hover { background: #1e1e1e; border-radius: 4px; }
            QListWidget::item { padding: 6px 8px; border-radius: 4px; }
        """)
        self.note_list.currentRowChanged.connect(self._load_note)
        left_layout.addWidget(self.note_list)

        new_btn = QPushButton("➕  Neue Notiz")
        new_btn.setStyleSheet(self.button_style())
        new_btn.clicked.connect(self._new_note)
        del_btn = QPushButton("🗑  Löschen")
        del_btn.setStyleSheet(self.button_style(False))
        del_btn.clicked.connect(self._delete_note)
        left_layout.addWidget(new_btn)
        left_layout.addWidget(del_btn)
        left.setMaximumWidth(220)

        # Right panel
        right = QFrame()
        right.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Title input
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titel...")
        self.title_input.setStyleSheet(self.input_style())
        self.title_input.setFont(QFont("Monospace", 12, QFont.Weight.Bold))
        self.title_input.textChanged.connect(self._mark_dirty)
        right_layout.addWidget(self.title_input)

        # Tags
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Tags (kommagetrennt, z.B. ssh, linux, config)...")
        self.tags_input.setStyleSheet(self.input_style())
        right_layout.addWidget(self.tags_input)

        # Editor
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Notiz, Command oder Config hier eingeben...")
        self.editor.setStyleSheet(self.input_style())
        self.editor.setFont(QFont("Monospace", 10))
        self.editor.textChanged.connect(self._mark_dirty)
        right_layout.addWidget(self.editor)

        # Save button
        save_row = QHBoxLayout()
        self.save_btn = QPushButton("💾  Speichern")
        self.save_btn.setStyleSheet(self.button_style())
        self.save_btn.clicked.connect(self._save_note)
        self.save_status = QLabel("")
        self.save_status.setStyleSheet(self.label_style(muted=True))
        export_btn = QPushButton("📤  Exportieren")
        export_btn.setStyleSheet(self.button_style(False))
        export_btn.clicked.connect(self._export)
        save_row.addWidget(self.save_btn)
        save_row.addWidget(export_btn)
        save_row.addWidget(self.save_status)
        save_row.addStretch()
        right_layout.addLayout(save_row)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([200, 600])
        self.content_layout.addWidget(splitter)

        self._load_from_disk()

    def _load_from_disk(self):
        try:
            if os.path.exists(NOTES_FILE):
                with open(NOTES_FILE) as f:
                    self._notes = json.load(f)
        except Exception:
            self._notes = {}
        self._refresh_list()

    def _save_to_disk(self):
        try:
            with open(NOTES_FILE, "w") as f:
                json.dump(self._notes, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _refresh_list(self, query: str = ""):
        self.note_list.clear()
        for key, note in sorted(self._notes.items(), key=lambda x: x[1].get("updated", ""), reverse=True):
            title = note.get("title", key)
            if query and query.lower() not in title.lower() and query.lower() not in note.get("tags", "").lower():
                continue
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.note_list.addItem(item)

    def _filter_list(self):
        self._refresh_list(self.search_input.text())

    def _new_note(self):
        key = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._notes[key] = {"title": "Neue Notiz", "content": "", "tags": "", "updated": key}
        self._refresh_list()
        self._current_key = key
        self.title_input.setText("Neue Notiz")
        self.editor.clear()
        self.tags_input.clear()
        self.title_input.setFocus()
        self._save_to_disk()

    def _load_note(self, _row: int):
        item = self.note_list.currentItem()
        if not item:
            return
        key = item.data(Qt.ItemDataRole.UserRole)
        self._current_key = key
        note = self._notes.get(key, {})
        self.title_input.blockSignals(True)
        self.editor.blockSignals(True)
        self.title_input.setText(note.get("title", ""))
        self.editor.setPlainText(note.get("content", ""))
        self.tags_input.setText(note.get("tags", ""))
        self.title_input.blockSignals(False)
        self.editor.blockSignals(False)
        self.save_status.setText("")

    def _save_note(self):
        if not self._current_key:
            return
        self._notes[self._current_key] = {
            "title": self.title_input.text() or "Ohne Titel",
            "content": self.editor.toPlainText(),
            "tags": self.tags_input.text(),
            "updated": datetime.now().isoformat()
        }
        self._save_to_disk()
        self._refresh_list()
        self.save_status.setText("✅ Gespeichert")

    def _delete_note(self):
        if not self._current_key:
            return
        reply = QMessageBox.question(self, "Löschen", "Notiz wirklich löschen?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self._notes[self._current_key]
            self._current_key = None
            self.title_input.clear()
            self.editor.clear()
            self.tags_input.clear()
            self._save_to_disk()
            self._refresh_list()

    def _mark_dirty(self):
        self.save_status.setText("● Ungespeichert")
        self.save_status.setStyleSheet("color: #ffaa00; font-family: Monospace; font-size: 9pt;")

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Notizen exportieren", filter="JSON (*.json);;Text (*.txt)")
        if path:
            with open(path, "w") as f:
                if path.endswith(".json"):
                    json.dump(self._notes, f, indent=2, ensure_ascii=False)
                else:
                    for note in self._notes.values():
                        f.write(f"# {note['title']}\n{note.get('content','')}\n\n---\n\n")
