"""Reusable UI widgets."""
from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor
from config import *


# ─── Helpers ──────────────────────────────────────────────────────────────────

def lbl(text: str = "", color: str = TEXT_PRI, size: int = 13,
        bold: bool = False, parent=None) -> QLabel:
    l = QLabel(text, parent)
    w = "600" if bold else "400"
    l.setStyleSheet(
        f"color:{color}; font-size:{size}px; font-weight:{w};"
        " background:transparent; border:none;"
    )
    return l


def section_label(text: str) -> QLabel:
    return lbl(text.upper(), TEXT_HINT, 10)


def mk_btn(text: str, bg: str = BLUE, fg: str = BG_DARK,
           border: str = "") -> QPushButton:
    b = QPushButton(text)
    border_css = f"border: 1px solid {border};" if border else "border: none;"
    b.setStyleSheet(
        f"QPushButton {{ background:{bg}; color:{fg}; {border_css}"
        f"  border-radius:6px; padding:5px 14px; font-size:12px; font-weight:600; }}"
        f"QPushButton:hover {{ background:{bg}dd; }}"
        f"QPushButton:disabled {{ background:#2a2a2a; color:#555; }}"
    )
    return b


def ghost_btn(text: str, fg: str = TEXT_SEC) -> QPushButton:
    b = QPushButton(text)
    b.setStyleSheet(
        f"QPushButton {{ background:{BG_CARD2}; color:{fg};"
        f"  border:1px solid {BORDER}; border-radius:6px;"
        f"  padding:5px 14px; font-size:12px; }}"
        f"QPushButton:hover {{ background:{BG_CARD3}; border-color:{BORDER_HVR}; }}"
    )
    return b


# ─── UsageBar ─────────────────────────────────────────────────────────────────

class UsageBar(QWidget):
    def __init__(self, value: float = 0, color: str = BLUE, parent=None):
        super().__init__(parent)
        self._value = value
        self._color = QColor(color)
        self.setFixedHeight(6)

    def set_value(self, v: float, color: str | None = None) -> None:
        self._value = max(0.0, min(100.0, v))
        if color:
            self._color = QColor(color)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(BORDER))
        p.drawRoundedRect(0, 0, self.width(), 6, 3, 3)
        w = int(self.width() * self._value / 100)
        if w > 0:
            p.setBrush(self._color)
            p.drawRoundedRect(0, 0, w, 6, 3, 3)


# ─── StatCard ─────────────────────────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, title: str, value: str = "–", sub: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER}; border-radius:12px; }}"
        )
        self.setMinimumHeight(100)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(4)

        t = QLabel(title.upper())
        t.setStyleSheet(
            f"color:{TEXT_HINT}; font-size:10px; font-weight:500;"
            " letter-spacing:1px; background:transparent; border:none;"
        )
        self._val = lbl(value, TEXT_PRI, 28, bold=True)
        self._sub = lbl(sub, TEXT_SEC, 12)

        lay.addWidget(t)
        lay.addWidget(self._val)
        lay.addWidget(self._sub)
        lay.addStretch()

    def update_value(self, value: str, sub: str = "", accent: bool = False) -> None:
        c = RED if accent else TEXT_PRI
        self._val.setStyleSheet(
            f"color:{c}; font-size:28px; font-weight:600; background:transparent; border:none;"
        )
        self._val.setText(value)
        self._sub.setText(sub)


# ─── SectionCard ─────────────────────────────────────────────────────────────

class SectionCard(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER}; border-radius:12px; }}"
        )
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(20, 16, 20, 16)
        self._lay.setSpacing(10)
        if title:
            self._lay.addWidget(section_label(title))

    @property
    def layout_(self) -> QVBoxLayout:
        return self._lay


# ─── Badge ────────────────────────────────────────────────────────────────────

class Badge(QLabel):
    def __init__(self, text: str, bg: str, fg: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            f"background:{bg}; color:{fg}; border-radius:4px;"
            " padding:2px 8px; font-size:10px; font-weight:600; border:none;"
        )