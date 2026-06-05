"""Docker containers page."""
from __future__ import annotations
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt

from config import *
from ui.widgets import lbl, StatCard, UsageBar, mk_btn, ghost_btn, Badge
from ui.dialogs import LogDialog
import core.docker_client as dc


# ─── Worker ───────────────────────────────────────────────────────────────────

class _DockerWorker(QThread):
    data_ready = pyqtSignal(list)
    error      = pyqtSignal(str)

    def run(self):
        try:
            self.data_ready.emit(dc.list_containers())
        except Exception as e:
            self.error.emit(str(e))


# ─── Container Card ───────────────────────────────────────────────────────────

class ContainerCard(QFrame):
    action = pyqtSignal(str, str)   # id, action

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self._id   = data["id"]
        self._name = data["name"]
        running    = data["status"] == "running"

        border = GREEN if running else BORDER
        self.setStyleSheet(
            f"QFrame {{ background:{BG_CARD}; border:1px solid {border}; border-radius:12px; }}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        dot = lbl("●", GREEN if running else "#555", 12)
        name_lbl = lbl(data["name"], TEXT_PRI, 13, bold=True)
        name_lbl.setMaximumWidth(200)
        bg_b = "#0a2a0a" if running else "#2a2a2a"
        fg_b = GREEN     if running else TEXT_HINT
        badge = Badge(data["status"].upper(), bg_b, fg_b)
        hdr.addWidget(dot); hdr.addWidget(name_lbl); hdr.addWidget(badge); hdr.addStretch()
        lay.addLayout(hdr)

        # Image + ports
        lay.addWidget(lbl(data["image"], TEXT_HINT, 11))
        if data["ports"]:
            lay.addWidget(lbl(f"🔌 {data['ports']}", TEXT_SEC, 11))

        # CPU / MEM bars
        if running and data["cpu"] > 0:
            lay.addLayout(self._bar_row("CPU", f"{data['cpu']}%", data["cpu"], BLUE))
        if running and data["mem"] > 0:
            lay.addLayout(self._bar_row("MEM", data["mem_str"], data["mem"], GREEN))

        # Buttons
        btn_row = QHBoxLayout(); btn_row.setSpacing(6)
        if running:
            stop_b = self._action_btn("⏹ Stop",    RED,    "stop")
            rst_b  = self._action_btn("🔄 Restart", ORANGE, "restart")
            btn_row.addWidget(stop_b); btn_row.addWidget(rst_b)
        else:
            btn_row.addWidget(self._action_btn("▶ Start", GREEN, "start"))
        logs_b = ghost_btn("📋 Logs")
        logs_b.clicked.connect(lambda: self.action.emit(self._id, "logs"))
        btn_row.addWidget(logs_b); btn_row.addStretch()
        lay.addLayout(btn_row)

    def _bar_row(self, label_text, value_text, pct, color):
        row = QVBoxLayout(); row.setSpacing(3)
        meta = QHBoxLayout()
        meta.addWidget(lbl(label_text, TEXT_HINT, 10))
        meta.addStretch()
        meta.addWidget(lbl(value_text, color, 10, bold=True))
        row.addLayout(meta)
        row.addWidget(UsageBar(pct, color))
        return row

    def _action_btn(self, text: str, color: str, action: str):
        b = mk_btn(text, f"{color}22", color)
        b.setStyleSheet(
            f"QPushButton {{ background:{color}18; color:{color};"
            f"  border:1px solid {color}44; border-radius:6px;"
            f"  padding:4px 12px; font-size:11px; font-weight:600; }}"
            f"QPushButton:hover {{ background:{color}30; }}"
        )
        b.clicked.connect(lambda: self.action.emit(self._id, action))
        return b


# ─── Docker Page ──────────────────────────────────────────────────────────────

class DockerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(lbl("🐳  Docker Container", TEXT_PRI, 22, bold=True))
        hdr.addStretch()
        self._status = lbl("", TEXT_HINT, 11)
        hdr.addWidget(self._status)
        ref = ghost_btn("🔄 Aktualisieren")
        ref.clicked.connect(self.refresh)
        hdr.addWidget(ref)
        lay.addLayout(hdr)

        # Stat cards
        self._s_total  = StatCard("Container", "–", "gesamt")
        self._s_run    = StatCard("Laufend",   "–", "aktiv")
        self._s_stop   = StatCard("Gestoppt",  "–", "inaktiv")
        self._s_images = StatCard("Images",    "–", "lokal")
        sr = QHBoxLayout()
        for c in [self._s_total, self._s_run, self._s_stop, self._s_images]:
            c.setMinimumHeight(90); sr.addWidget(c)
        lay.addLayout(sr)

        # Grid scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        self._grid_w = QWidget(); self._grid_w.setStyleSheet("background:transparent;")
        self._grid   = QGridLayout(self._grid_w)
        self._grid.setSpacing(12); self._grid.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._grid_w)
        lay.addWidget(scroll)

        self._err = lbl("", RED, 13); self._err.hide(); lay.addWidget(self._err)

        # Auto-refresh
        self._timer = QTimer(); self._timer.timeout.connect(self.refresh); self._timer.start(REFRESH_DOCKER)
        self.refresh()

    def refresh(self):
        if not dc.is_available():
            self._err.setText("❌ Docker nicht erreichbar"); self._err.show(); return
        self._status.setText("Lädt…")
        w = _DockerWorker()
        w.data_ready.connect(self._on_data)
        w.error.connect(lambda e: (self._err.setText(f"❌ {e}"), self._err.show()))
        w.start()
        self._worker = w   # keep ref

    def _on_data(self, containers: list):
        running = [c for c in containers if c["status"] == "running"]
        stopped = [c for c in containers if c["status"] != "running"]
        self._s_total.update_value(str(len(containers)), "gesamt")
        self._s_run.update_value(str(len(running)), "aktiv")
        self._s_stop.update_value(str(len(stopped)), "inaktiv")
        try:
            self._s_images.update_value(str(len(dc.list_images())), "lokal")
        except Exception:
            pass

        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        cols = 2
        for i, c in enumerate(containers):
            card = ContainerCard(c)
            card.action.connect(self._on_action)
            self._grid.addWidget(card, i // cols, i % cols)

        if not containers:
            self._grid.addWidget(lbl("Keine Container gefunden", TEXT_HINT, 14), 0, 0)

        self._err.hide()
        self._status.setText(f"Aktualisiert: {datetime.now().strftime('%H:%M:%S')}")

    def _on_action(self, cid: str, action: str):
        try:
            if action == "logs":
                logs = dc.get_logs(cid)
                LogDialog(cid, logs, self).exec()
                return
            dc.container_action(cid, action)
            QTimer.singleShot(1500, self.refresh)
        except Exception as e:
            self._err.setText(f"❌ {e}"); self._err.show()