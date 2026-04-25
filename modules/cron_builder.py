from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QGridLayout,
    QCheckBox, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication
from modules.base_widget import BaseModuleWidget
from datetime import datetime, timedelta


PRESETS = {
    "Jede Minute":          "* * * * *",
    "Jede Stunde":          "0 * * * *",
    "Täglich 00:00":        "0 0 * * *",
    "Täglich 08:00":        "0 8 * * *",
    "Jeden Montag 08:00":   "0 8 * * 1",
    "Wöchentlich (So)":     "0 0 * * 0",
    "Monatlich (1.)":       "0 0 1 * *",
    "Jährlich (1. Jan)":    "0 0 1 1 *",
    "Alle 5 Minuten":       "*/5 * * * *",
    "Alle 15 Minuten":      "*/15 * * * *",
    "Alle 30 Minuten":      "*/30 * * * *",
    "Werktags 08:00":       "0 8 * * 1-5",
    "Wochenende 10:00":     "0 10 * * 6,0",
}

WEEKDAYS = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"]


class CronField(QLineEdit):
    """QLineEdit that clears '*' on focus and restores it when left empty."""

    def __init__(self, parent=None):
        super().__init__("*", parent)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.text() == "*":
            self.clear()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.text().strip() == "":
            self.setText("*")
MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def parse_cron(expr: str) -> str:
    """Generate a human-readable description from a cron expression."""
    parts = expr.strip().split()
    if len(parts) != 5:
        return "Ungültiger Cron-Ausdruck (5 Felder erwartet)"

    minute, hour, day, month, weekday = parts

    def fmt(val, unit, names=None):
        if val == "*":
            return f"jede/n {unit}"
        if val.startswith("*/"):
            return f"alle {val[2:]} {unit}"
        if "-" in val:
            parts = val.split("-", 1)
            a, b = parts[0], parts[1]
            try:
                if names:
                    return f"{names[int(a)]} bis {names[int(b)]}"
            except (ValueError, IndexError):
                pass
            return f"{unit} {a}–{b}"
        if "," in val:
            vals = val.split(",")
            try:
                if names:
                    return ", ".join(names[int(v)] for v in vals)
            except (ValueError, IndexError):
                pass
            return f"{unit} {', '.join(vals)}"
        try:
            if names:
                return names[int(val)]
        except (ValueError, IndexError):
            pass
        return f"{unit} {val}"

    parts_desc = []
    if minute != "*" or hour != "*":
        if minute.isdigit() and hour.isdigit():
            parts_desc.append(f"um {int(hour):02d}:{int(minute):02d} Uhr")
        else:
            parts_desc.append(fmt(minute, "Minute"))
            parts_desc.append(fmt(hour, "Stunde"))
    else:
        parts_desc.append("jede Minute")

    if weekday != "*":
        parts_desc.append(f"am {fmt(weekday, 'Wochentag', WEEKDAYS)}")
    elif day != "*":
        parts_desc.append(f"am {fmt(day, 'Tag')} des Monats")

    if month != "*":
        parts_desc.append(f"im {fmt(month, 'Monat', MONTHS)}")

    return "Ausführung: " + ", ".join(parts_desc)


class CronBuilderWidget(BaseModuleWidget):
    MODULE_TITLE = "⏰ Cron-Expression Builder"
    MODULE_SUBTITLE = "Cron-Ausdrücke erstellen, erklären & testen"

    def setup_ui(self):
        # Manual expression input
        expr_row = QHBoxLayout()
        self.expr_input = QLineEdit()
        self.expr_input.setPlaceholderText("Cron-Ausdruck eingeben, z.B.  */5 * * * *")
        self.expr_input.setStyleSheet(self.input_style())
        self.expr_input.setFont(QFont("Monospace", 12))
        self.expr_input.textChanged.connect(self._update_from_expr)

        copy_btn = QPushButton("📋")
        copy_btn.setFixedWidth(40)
        copy_btn.setStyleSheet(self.button_style(False))
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.expr_input.text()))

        expr_row.addWidget(self.expr_input)
        expr_row.addWidget(copy_btn)
        self.content_layout.addLayout(expr_row)

        # Human-readable description
        self.desc_label = QLabel("Beschreibung erscheint hier...")
        self.desc_label.setFont(QFont("Monospace", 10))
        self.desc_label.setStyleSheet("color: #00ff88; padding: 8px 0;")
        self.desc_label.setWordWrap(True)
        self.content_layout.addWidget(self.desc_label)

        # Visual builder
        builder_frame = QFrame()
        builder_frame.setStyleSheet(self.card_style())
        builder_layout = QGridLayout(builder_frame)
        builder_layout.setContentsMargins(20, 16, 20, 16)
        builder_layout.setSpacing(12)

        fields = [
            ("Minute", "0-59", "minute"),
            ("Stunde", "0-23", "hour"),
            ("Tag (Monat)", "1-31", "day"),
            ("Monat", "1-12", "month"),
            ("Wochentag", "0-6 (So=0)", "weekday"),
        ]
        self._field_inputs = {}
        for i, (label, hint, key) in enumerate(fields):
            lbl = QLabel(label)
            lbl.setFont(QFont("Monospace", 9, QFont.Weight.Bold))
            lbl.setStyleSheet("color: #a0a0a0; background: transparent; border: none;")

            hint_lbl = QLabel(hint)
            hint_lbl.setFont(QFont("Monospace", 8))
            hint_lbl.setStyleSheet("color: #444; background: transparent; border: none;")

            inp = CronField()
            inp.setFixedWidth(100)
            inp.setStyleSheet(self.input_style())
            inp.textChanged.connect(self._update_from_fields)

            builder_layout.addWidget(lbl, 0, i)
            builder_layout.addWidget(hint_lbl, 1, i)
            builder_layout.addWidget(inp, 2, i)
            self._field_inputs[key] = inp

        self.content_layout.addWidget(builder_frame)

        # Presets
        presets_frame = QFrame()
        presets_frame.setStyleSheet(self.card_style())
        presets_layout = QVBoxLayout(presets_frame)
        presets_layout.setContentsMargins(16, 14, 16, 14)
        presets_layout.setSpacing(8)

        preset_lbl = QLabel("Schnell-Vorlagen:")
        preset_lbl.setStyleSheet(self.label_style())
        presets_layout.addWidget(preset_lbl)

        grid = QGridLayout()
        grid.setSpacing(8)
        for i, (name, expr) in enumerate(PRESETS.items()):
            btn = QPushButton(name)
            btn.setStyleSheet(self.button_style(False))
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda _, e=expr: self._set_expr(e))
            grid.addWidget(btn, i // 4, i % 4)
        presets_layout.addLayout(grid)
        self.content_layout.addWidget(presets_frame)

        # Next executions
        next_frame = QFrame()
        next_frame.setStyleSheet(self.card_style())
        next_layout = QVBoxLayout(next_frame)
        next_layout.setContentsMargins(16, 14, 16, 14)
        next_lbl = QLabel("Nächste Ausführungen (simuliert):")
        next_lbl.setStyleSheet(self.label_style())
        next_layout.addWidget(next_lbl)
        self.next_label = QLabel("—")
        self.next_label.setFont(QFont("Monospace", 9))
        self.next_label.setStyleSheet("color: #a0a0a0; background: transparent; border: none;")
        self.next_label.setWordWrap(True)
        next_layout.addWidget(self.next_label)
        self.content_layout.addWidget(next_frame)

        self._set_expr("* * * * *")

    def _set_expr(self, expr: str):
        self.expr_input.blockSignals(True)
        self.expr_input.setText(expr)
        self.expr_input.blockSignals(False)
        self._update_from_expr(expr)

    def _update_from_expr(self, expr: str):
        parts = expr.strip().split()
        keys = ["minute", "hour", "day", "month", "weekday"]
        if len(parts) == 5:
            for key, val in zip(keys, parts):
                self._field_inputs[key].blockSignals(True)
                self._field_inputs[key].setText(val)
                self._field_inputs[key].blockSignals(False)
            self.desc_label.setText(parse_cron(expr))
            self.desc_label.setStyleSheet("color: #00ff88; padding: 8px 0; font-family: Monospace;")
            self._compute_next(parts)
        else:
            self.desc_label.setText("⚠️  Ungültiger Ausdruck — 5 Felder benötigt")
            self.desc_label.setStyleSheet("color: #ff4444; padding: 8px 0; font-family: Monospace;")

    def _update_from_fields(self):
        keys = ["minute", "hour", "day", "month", "weekday"]
        expr = " ".join(self._field_inputs[k].text() or "*" for k in keys)
        self.expr_input.blockSignals(True)
        self.expr_input.setText(expr)
        self.expr_input.blockSignals(False)
        self._update_from_expr(expr)

    def _compute_next(self, parts: list[str]):
        """Simple next-execution simulator for common patterns."""
        try:
            minute, hour, day, month, weekday = parts
            now = datetime.now().replace(second=0, microsecond=0)
            results = []
            t = now + timedelta(minutes=1)
            checked = 0
            while len(results) < 5 and checked < 50000:
                checked += 1
                m_ok = minute == "*" or (minute.startswith("*/") and t.minute % int(minute[2:]) == 0) or str(t.minute) == minute
                h_ok = hour == "*" or (hour.startswith("*/") and t.hour % int(hour[2:]) == 0) or str(t.hour) == hour
                d_ok = day == "*" or str(t.day) == day
                mo_ok = month == "*" or str(t.month) == month
                wd_ok = weekday == "*" or str(t.weekday() + 1 if t.weekday() < 6 else 0) == weekday
                if m_ok and h_ok and d_ok and mo_ok and wd_ok:
                    results.append(t.strftime("%a %d.%m.%Y %H:%M"))
                t += timedelta(minutes=1)
            self.next_label.setText("\n".join(f"→  {r}" for r in results))
        except Exception:
            self.next_label.setText("Simulation nicht möglich für diesen Ausdruck.")
