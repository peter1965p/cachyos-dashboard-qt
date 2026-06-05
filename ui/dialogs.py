"""Reusable dialogs."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QLabel
)
from PyQt6.QtGui import QTextCursor, QFont
from PyQt6.QtCore import Qt, QTimer
from config import *
from ui.widgets import mk_btn, ghost_btn, lbl


class LogDialog(QDialog):
    def __init__(self, title: str, logs: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Logs — {title}")
        self.resize(960, 640)
        self.setStyleSheet(f"background:{BG_DARK}; color:{TEXT_PRI};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        hdr = QHBoxLayout()
        hdr.addWidget(lbl(f"📋  {title}", TEXT_PRI, 14, bold=True))
        hdr.addStretch()
        lay.addLayout(hdr)

        self._txt = QPlainTextEdit()
        self._txt.setReadOnly(True)
        self._txt.setPlainText(logs)
        self._txt.setStyleSheet(
            f"background:#050505; color:{GREEN};"
            f"border:1px solid {BORDER}; border-radius:8px;"
            "font-family:'JetBrains Mono','Fira Code',monospace; font-size:11px; padding:8px;"
        )
        self._txt.moveCursor(QTextCursor.MoveOperation.End)
        lay.addWidget(self._txt)

        footer = QHBoxLayout()
        copy_btn = ghost_btn("📋 Kopieren")
        copy_btn.clicked.connect(self._copy)
        close_btn = mk_btn("Schließen", BG_CARD2, TEXT_PRI)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(copy_btn)
        footer.addStretch()
        footer.addWidget(close_btn)
        lay.addLayout(footer)

    def _copy(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._txt.toPlainText())


class ConfirmDialog(QDialog):
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bestätigung")
        self.setFixedSize(380, 160)
        self.setStyleSheet(f"background:{BG_CARD}; color:{TEXT_PRI};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(20)
        lay.addWidget(lbl(message, TEXT_PRI, 13))

        btns = QHBoxLayout()
        cancel = ghost_btn("Abbrechen")
        cancel.clicked.connect(self.reject)
        ok = mk_btn("OK", RED, TEXT_PRI)
        ok.clicked.connect(self.accept)
        btns.addWidget(cancel); btns.addStretch(); btns.addWidget(ok)
        lay.addLayout(btns)