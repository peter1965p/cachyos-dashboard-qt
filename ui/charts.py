"""Performance chart widget."""
from __future__ import annotations
from collections import deque

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor, QLinearGradient
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QAreaSeries, QValueAxis
from PyQt6.QtCore import QMargins

from config import *
from ui.widgets import lbl, section_label


class PerfChart(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER}; border-radius:12px; }}"
        )
        self.setMinimumHeight(220)
        self._cpu = deque([0.0] * 40, maxlen=40)
        self._ram = deque([0.0] * 40, maxlen=40)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 8)

        # Header row
        hdr = QHBoxLayout()
        hdr.addWidget(section_label("System Performance"))
        hdr.addStretch()
        for color, text in [(BLUE, "CPU %"), (GREEN, "RAM %")]:
            dot = lbl("●", color, 12)
            hdr.addWidget(dot)
            hdr.addWidget(lbl(text, TEXT_SEC, 11))
        lay.addLayout(hdr)

        # Series
        self._cpu_s = QLineSeries()
        self._ram_s = QLineSeries()
        p1 = QPen(QColor(BLUE));  p1.setWidth(2); self._cpu_s.setPen(p1)
        p2 = QPen(QColor(GREEN)); p2.setWidth(2); self._ram_s.setPen(p2)

        cpu_area = QAreaSeries(self._cpu_s)
        ram_area = QAreaSeries(self._ram_s)

        g1 = QLinearGradient(0, 0, 0, 1)
        g1.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        g1.setColorAt(0, QColor(137, 180, 250, 55))
        g1.setColorAt(1, QColor(137, 180, 250, 0))

        g2 = QLinearGradient(0, 0, 0, 1)
        g2.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        g2.setColorAt(0, QColor(166, 227, 161, 55))
        g2.setColorAt(1, QColor(166, 227, 161, 0))

        cpu_area.setBrush(g1); cpu_area.setPen(QPen(Qt.PenStyle.NoPen))
        ram_area.setBrush(g2); ram_area.setPen(QPen(Qt.PenStyle.NoPen))

        chart = QChart()
        for s in [cpu_area, ram_area, self._cpu_s, self._ram_s]:
            chart.addSeries(s)
        chart.setBackgroundBrush(QColor(0, 0, 0, 0))
        chart.setBackgroundRoundness(0)
        chart.legend().hide()
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.layout().setContentsMargins(0, 0, 0, 0)

        ax_x = QValueAxis(); ax_x.setRange(0, 39); ax_x.setVisible(False)
        ax_y = QValueAxis(); ax_y.setRange(0, 100); ax_y.setTickCount(5)
        ax_y.setLabelsColor(QColor(TEXT_HINT))
        ax_y.setGridLineColor(QColor(BORDER))
        ax_y.setLinePenColor(QColor(0, 0, 0, 0))
        chart.addAxis(ax_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(ax_y, Qt.AlignmentFlag.AlignLeft)
        for s in [cpu_area, ram_area, self._cpu_s, self._ram_s]:
            s.attachAxis(ax_x); s.attachAxis(ax_y)

        view = QChartView(chart)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.setStyleSheet("background:transparent; border:none;")
        lay.addWidget(view)

        for i in range(40):
            self._cpu_s.append(i, 0)
            self._ram_s.append(i, 0)

    def push(self, cpu: float, ram: float) -> None:
        self._cpu.append(cpu)
        self._ram.append(ram)
        self._cpu_s.clear(); self._ram_s.clear()
        for i, (c, r) in enumerate(zip(self._cpu, self._ram)):
            self._cpu_s.append(i, c)
            self._ram_s.append(i, r)