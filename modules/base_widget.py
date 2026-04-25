from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class BaseModuleWidget(QWidget):
    """
    Base class for all FISI Toolbox modules.
    Provides consistent header and layout styling.
    """

    MODULE_TITLE = "Module"
    MODULE_SUBTITLE = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #0d0d0d; color: #e0e0e0;")
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(32, 28, 32, 28)
        self._outer.setSpacing(0)

        self._build_header()
        self._build_divider()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 20, 0, 0)
        self.content_layout.setSpacing(16)
        self._outer.addLayout(self.content_layout)
        self.setup_ui()

    def _build_header(self):
        title = QLabel(self.MODULE_TITLE)
        title.setFont(QFont("Monospace", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #00ff88;")
        self._outer.addWidget(title)

        if self.MODULE_SUBTITLE:
            sub = QLabel(self.MODULE_SUBTITLE)
            sub.setFont(QFont("Monospace", 9))
            sub.setStyleSheet("color: #555; margin-top: 2px;")
            self._outer.addWidget(sub)

        self._outer.addSpacing(12)

    def _build_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #1e1e1e; background: #1e1e1e;")
        line.setFixedHeight(1)
        self._outer.addWidget(line)

    def setup_ui(self):
        """Override in subclasses to build module-specific UI."""
        pass

    # ── Style helpers ────────────────────────────────────────────────────────

    @staticmethod
    def input_style() -> str:
        return """
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
                background: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 8px 12px;
                font-family: Monospace;
                font-size: 10pt;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
            QSpinBox:focus, QComboBox:focus {
                border: 1px solid #00ff88;
            }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { color: #00ff88; }
        """

    @staticmethod
    def button_style(accent: bool = True) -> str:
        if accent:
            return """
                QPushButton {
                    background: #00ff88;
                    color: #0a0a0a;
                    border: none;
                    border-radius: 6px;
                    padding: 9px 20px;
                    font-family: Monospace;
                    font-size: 10pt;
                    font-weight: bold;
                }
                QPushButton:hover { background: #00e87a; }
                QPushButton:pressed { background: #00cc6a; }
                QPushButton:disabled { background: #1e1e1e; color: #444; }
            """
        return """
            QPushButton {
                background: #1a1a1a;
                color: #a0a0a0;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 9px 20px;
                font-family: Monospace;
                font-size: 10pt;
            }
            QPushButton:hover { background: #222; color: #fff; border-color: #444; }
            QPushButton:pressed { background: #111; }
        """

    @staticmethod
    def output_style() -> str:
        return """
            QTextEdit, QPlainTextEdit {
                background: #111111;
                color: #00ff88;
                border: 1px solid #1e1e1e;
                border-radius: 6px;
                padding: 12px;
                font-family: Monospace;
                font-size: 9pt;
            }
        """

    @staticmethod
    def table_style() -> str:
        return """
            QTableWidget {
                background: #111111;
                color: #e0e0e0;
                gridline-color: #1e1e1e;
                border: 1px solid #1e1e1e;
                border-radius: 6px;
                font-family: Monospace;
                font-size: 9pt;
            }
            QTableWidget::item:selected {
                background: #00ff8830;
                color: #00ff88;
            }
            QHeaderView::section {
                background: #1a1a1a;
                color: #00ff88;
                border: none;
                padding: 6px 12px;
                font-family: Monospace;
                font-size: 9pt;
                font-weight: bold;
            }
        """

    @staticmethod
    def label_style(muted: bool = False) -> str:
        color = "#555" if muted else "#a0a0a0"
        return f"color: {color}; font-family: Monospace; font-size: 9pt;"

    @staticmethod
    def card_style() -> str:
        return """
            QFrame {
                background: #111111;
                border: 1px solid #1e1e1e;
                border-radius: 8px;
                padding: 12px;
            }
        """
