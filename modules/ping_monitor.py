import subprocess
import re
import time
from collections import deque
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen
from modules.base_widget import BaseModuleWidget


class PingThread(QThread):
    result = pyqtSignal(float, bool)  # ms, success

    def __init__(self, host: str):
        super().__init__()
        self.host = host
        self._running = True

    def run(self):
        while self._running:
            try:
                proc = subprocess.run(
                    ["ping", "-c", "1", "-W", "2", self.host],
                    capture_output=True, text=True
                )
                match = re.search(r"time=([\d.]+)", proc.stdout)
                if match:
                    self.result.emit(float(match.group(1)), True)
                else:
                    self.result.emit(0.0, False)
            except Exception:
                self.result.emit(0.0, False)
            time.sleep(1)

    def stop(self):
        self._running = False


class PingGraph(QFrame):
    MAX_POINTS = 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: #111111; border: 1px solid #1e1e1e; border-radius: 8px;")
        self._data: deque[tuple[float, bool]] = deque(maxlen=self.MAX_POINTS)

    def add_point(self, ms: float, success: bool):
        self._data.append((ms, success))
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        pad = 16

        # Grid lines
        painter.setPen(QPen(QColor("#1e1e1e"), 1))
        for i in range(1, 4):
            y = pad + (h - pad * 2) * i // 4
            painter.drawLine(pad, y, w - pad, y)

        values = [ms for ms, ok in self._data if ok]
        if not values:
            return
        max_val = max(values) * 1.2 or 100

        points = list(self._data)
        total = self.MAX_POINTS
        step = (w - pad * 2) / total

        # Draw line
        painter.setPen(QPen(QColor("#00ff88"), 2))
        prev = None
        for i, (ms, ok) in enumerate(points):
            x = int(pad + (total - len(points) + i) * step)
            if ok:
                y = int(h - pad - (ms / max_val) * (h - pad * 2))
                if prev:
                    painter.drawLine(prev[0], prev[1], x, y)
                prev = (x, y)
            else:
                painter.setPen(QPen(QColor("#ff4444"), 2))
                y = h - pad
                if prev:
                    painter.drawLine(prev[0], prev[1], x, y)
                painter.setPen(QPen(QColor("#00ff88"), 2))
                prev = None

        # Max label
        painter.setPen(QColor("#555"))
        painter.setFont(QFont("Monospace", 8))
        painter.drawText(pad, pad + 12, f"{max_val:.0f} ms")

        painter.end()


class PingMonitorWidget(BaseModuleWidget):
    MODULE_TITLE = "📡 Ping Monitor"
    MODULE_SUBTITLE = "Kontinuierlicher Ping mit Live-Graph"

    def setup_ui(self):
        # Input row
        row = QHBoxLayout()
        row.setSpacing(10)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Host oder IP...")
        self.host_input.setStyleSheet(self.input_style())
        self.host_input.setText("8.8.8.8")

        self.start_btn = QPushButton("▶  Start")
        self.start_btn.setStyleSheet(self.button_style())
        self.start_btn.setFixedWidth(110)
        self.start_btn.clicked.connect(self._start)

        self.stop_btn = QPushButton("■  Stop")
        self.stop_btn.setStyleSheet(self.button_style(False))
        self.stop_btn.setFixedWidth(90)
        self.stop_btn.clicked.connect(self._stop)
        self.stop_btn.setEnabled(False)

        row.addWidget(self.host_input)
        row.addWidget(self.start_btn)
        row.addWidget(self.stop_btn)
        self.content_layout.addLayout(row)

        # Stats cards
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self._stat_widgets = {}
        for key, label in [("current", "Aktuell"), ("min", "Min"), ("avg", "Ø Avg"), ("max", "Max"), ("loss", "Verlust")]:
            card = QFrame()
            card.setStyleSheet("background: #111; border: 1px solid #1e1e1e; border-radius: 8px; padding: 8px;")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            lbl = QLabel(label)
            lbl.setFont(QFont("Monospace", 8))
            lbl.setStyleSheet("color: #555; border: none;")
            val = QLabel("—")
            val.setFont(QFont("Monospace", 14, QFont.Weight.Bold))
            val.setStyleSheet("color: #00ff88; border: none;")
            card_layout.addWidget(lbl)
            card_layout.addWidget(val)
            stats_row.addWidget(card)
            self._stat_widgets[key] = val
        self.content_layout.addLayout(stats_row)

        # Graph
        self.graph = PingGraph()
        self.content_layout.addWidget(self.graph)

        self._thread = None
        self._times = []
        self._sent = 0
        self._lost = 0

    def _start(self):
        host = self.host_input.text().strip()
        if not host:
            return
        self._times.clear()
        self._sent = 0
        self._lost = 0
        self.graph._data.clear()
        self.graph.update()

        self._thread = PingThread(host)
        self._thread.result.connect(self._on_result)
        self._thread.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _on_result(self, ms: float, ok: bool):
        self._sent += 1
        if ok:
            self._times.append(ms)
            self._stat_widgets["current"].setText(f"{ms:.1f} ms")
            self._stat_widgets["min"].setText(f"{min(self._times):.1f} ms")
            self._stat_widgets["avg"].setText(f"{sum(self._times)/len(self._times):.1f} ms")
            self._stat_widgets["max"].setText(f"{max(self._times):.1f} ms")
        else:
            self._lost += 1
            self._stat_widgets["current"].setText("Timeout")
            self._stat_widgets["current"].setStyleSheet("color: #ff4444; border: none; font-family: Monospace; font-size: 14pt; font-weight: bold;")

        loss_pct = (self._lost / self._sent * 100) if self._sent else 0
        self._stat_widgets["loss"].setText(f"{loss_pct:.1f}%")
        self.graph.add_point(ms, ok)

    def _stop(self):
        if self._thread:
            self._thread.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
