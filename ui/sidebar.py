"""Sidebar navigation."""
from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from config import *


class _SideBtn(QPushButton):
    def __init__(self, emoji: str, tooltip: str):
        super().__init__(emoji)
        self.setToolTip(tooltip)
        self.setFixedSize(42, 42)
        self.setCheckable(True)
        self._apply(False)

    def _apply(self, active: bool):
        bg = "#1e3a5f" if active else "transparent"
        bd = f"border:1px solid {BLUE};" if active else "border:none;"
        self.setStyleSheet(
            f"QPushButton {{ background:{bg}; {bd} border-radius:8px;"
            f"  font-size:20px; color:white; }}"
            f"QPushButton:hover {{ background:#1a2a3a; border-radius:8px; }}"
        )

    def setChecked(self, v: bool):
        super().setChecked(v)
        self._apply(v)


class Sidebar(QWidget):
    page_changed = pyqtSignal(int)

    PAGES = [
        ("📊", "Dashboard"),
        ("🐳", "Docker Container"),
        ("📦", "Compose Manager"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(SIDEBAR_W)
        self.setStyleSheet(f"background:#080808; border-right:1px solid {BORDER};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(7, 16, 7, 16)
        lay.setSpacing(8)

        logo = QLabel("🐧")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size:24px; background:transparent; border:none;")
        lay.addWidget(logo)
        lay.addSpacing(16)

        self._btns: list[_SideBtn] = []
        for i, (emoji, tip) in enumerate(self.PAGES):
            b = _SideBtn(emoji, tip)
            b.clicked.connect(lambda _, idx=i: self._select(idx))
            lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            self._btns.append(b)

        lay.addStretch()
        self._select(0)

    def _select(self, idx: int):
        for i, b in enumerate(self._btns):
            b.setChecked(i == idx)
        self.page_changed.emit(idx)