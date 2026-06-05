"""Docker Hub search widget with live results."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QLineEdit, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from config import *
from ui.widgets import lbl, mk_btn, ghost_btn, Badge
from core.docker_client import search_hub


# ─── Search Worker ────────────────────────────────────────────────────────────

class _SearchWorker(QThread):
    results_ready = pyqtSignal(list)

    def __init__(self, query: str):
        super().__init__()
        self._query = query

    def run(self):
        results = search_hub(self._query, limit=8)
        self.results_ready.emit(results)


# ─── Result Row ───────────────────────────────────────────────────────────────

class _ResultRow(QFrame):
    selected = pyqtSignal(dict)   # emits the result dict

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self._data = data
        self.setStyleSheet(
            f"QFrame {{ background:{BG_CARD2}; border:none;"
            f"  border-bottom:1px solid {BORDER}; }}"
            f"QFrame:hover {{ background:{BG_CARD3}; }}"
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)

        info = QVBoxLayout()
        info.setSpacing(2)

        name_row = QHBoxLayout()
        name_row.setSpacing(6)
        name_lbl = lbl(data["name"], TEXT_PRI, 12, bold=True)
        name_lbl.setMaximumWidth(260)
        name_row.addWidget(name_lbl)
        if data["official"]:
            name_row.addWidget(Badge("OFFICIAL", "#1e3a5f", BLUE))
        name_row.addStretch()
        info.addLayout(name_row)

        desc = data["description"] or "No description"
        desc_lbl = lbl(desc[:80] + ("…" if len(desc) > 80 else ""), TEXT_HINT, 10)
        info.addWidget(desc_lbl)
        lay.addLayout(info, 1)

        meta = QVBoxLayout()
        meta.setSpacing(2)
        meta.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        stars = data.get("stars", 0)
        meta.addWidget(lbl(f"⭐ {stars:,}", TEXT_HINT, 10), alignment=Qt.AlignmentFlag.AlignRight)
        lay.addLayout(meta)

        sel_btn = mk_btn("Auswählen", PURPLE, BG_DARK)
        sel_btn.setFixedWidth(90)
        sel_btn.clicked.connect(lambda: self.selected.emit(self._data))
        lay.addWidget(sel_btn)

    def mousePressEvent(self, _):
        self.selected.emit(self._data)


# ─── Hub Search Widget ────────────────────────────────────────────────────────

class HubSearchWidget(QWidget):
    image_selected = pyqtSignal(dict)   # user picked an image

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self._worker: _SearchWorker | None = None
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._do_search)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        # Search bar
        bar = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("🔍  Docker Hub durchsuchen…  (z.B. nginx, redis, postgres)")
        self._input.setStyleSheet(
            f"QLineEdit {{ background:{BG_CARD2}; color:{TEXT_PRI};"
            f"  border:1px solid {BORDER}; border-radius:8px;"
            f"  padding:8px 12px; font-size:13px; }}"
            f"QLineEdit:focus {{ border:1px solid {BLUE}; }}"
        )
        self._input.textChanged.connect(self._on_text_changed)
        bar.addWidget(self._input)
        self._status = lbl("", TEXT_HINT, 11)
        bar.addWidget(self._status)
        lay.addLayout(bar)

        # Results panel (hidden by default)
        self._results_frame = QFrame()
        self._results_frame.setStyleSheet(
            f"QFrame {{ background:{BG_CARD2}; border:1px solid {BORDER}; border-radius:8px; }}"
        )
        self._results_frame.hide()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(280)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background:transparent;")
        self._list_lay = QVBoxLayout(self._list_widget)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(0)
        scroll.setWidget(self._list_widget)

        rf_lay = QVBoxLayout(self._results_frame)
        rf_lay.setContentsMargins(0, 0, 0, 0)
        rf_lay.addWidget(scroll)
        lay.addWidget(self._results_frame)

    def _on_text_changed(self, text: str):
        self._debounce.stop()
        if not text.strip():
            self._results_frame.hide()
            self._status.setText("")
            return
        self._debounce.start(400)

    def _do_search(self):
        query = self._input.text().strip()
        if not query:
            return
        self._status.setText("Suche…")
        self._worker = _SearchWorker(query)
        self._worker.results_ready.connect(self._show_results)
        self._worker.start()

    def _show_results(self, results: list):
        # Clear old rows
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not results:
            self._list_lay.addWidget(lbl("Keine Ergebnisse", TEXT_HINT, 12))
        else:
            for r in results:
                row = _ResultRow(r)
                row.selected.connect(self._on_selected)
                self._list_lay.addWidget(row)

        self._list_lay.addStretch()
        self._results_frame.show()
        self._status.setText(f"{len(results)} Ergebnisse")

    def _on_selected(self, data: dict):
        self._input.clear()
        self._results_frame.hide()
        self._status.setText("")
        self.image_selected.emit(data)

    def clear(self):
        self._input.clear()
        self._results_frame.hide()