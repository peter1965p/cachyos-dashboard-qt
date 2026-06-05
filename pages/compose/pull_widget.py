"""Pull progress widget with animated purple progress bar."""
from __future__ import annotations
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QLinearGradient
from config import *
from ui.widgets import lbl, mk_btn, ghost_btn, Badge
from core.docker_client import pull_image


# ─── Pull Worker ─────────────────────────────────────────────────────────────

class PullWorker(QThread):
    finished = pyqtSignal(bool, str)   # success, error_msg

    def __init__(self, image: str, tag: str):
        super().__init__()
        self._image = image
        self._tag   = tag

    def run(self):
        try:
            pull_image(self._image, self._tag)
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))


# ─── Animated Progress Bar ────────────────────────────────────────────────────

class PurpleProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self._value  = 0.0
        self._anim_x = 0.0   # shimmer position

        self._shimmer = QTimer()
        self._shimmer.timeout.connect(self._tick_shimmer)

    def set_value(self, v: float):
        self._value = max(0.0, min(100.0, v))
        self.update()

    def start_shimmer(self):
        self._shimmer.start(30)

    def stop_shimmer(self):
        self._shimmer.stop()

    def _tick_shimmer(self):
        self._anim_x = (self._anim_x + 2) % (self.width() + 60)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        # Track
        p.setBrush(QColor(BORDER))
        p.drawRoundedRect(0, 0, self.width(), 8, 4, 4)

        # Fill
        w = int(self.width() * self._value / 100)
        if w <= 0:
            return

        fill = QLinearGradient(0, 0, w, 0)
        fill.setColorAt(0.0, QColor(PURPLE))
        fill.setColorAt(1.0, QColor("#b380ff"))
        p.setBrush(fill)
        p.drawRoundedRect(0, 0, w, 8, 4, 4)

        # Shimmer overlay
        if self._shimmer.isActive():
            shim = QLinearGradient(self._anim_x - 40, 0, self._anim_x + 40, 0)
            shim.setColorAt(0.0, QColor(255, 255, 255, 0))
            shim.setColorAt(0.5, QColor(255, 255, 255, 55))
            shim.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(shim)
            p.drawRoundedRect(0, 0, w, 8, 4, 4)


# ─── Single Pull Card ─────────────────────────────────────────────────────────

class PullCard(QFrame):
    done       = pyqtSignal(str, str)    # image:tag, status ("done"|"error")
    load_preset = pyqtSignal(str)        # image:tag — load default config
    removed    = pyqtSignal(str)         # id

    STATUS_PREVIEW  = "preview"
    STATUS_PULLING  = "pulling"
    STATUS_DONE     = "done"
    STATUS_ERROR    = "error"

    def __init__(self, image: str, tag: str, description: str = "", parent=None):
        super().__init__(parent)
        self.id      = str(uuid.uuid4())[:8]
        self._image  = image
        self._tag    = tag
        self._status = self.STATUS_PREVIEW
        self._worker: PullWorker | None = None
        self._fake_timer = QTimer()
        self._fake_timer.timeout.connect(self._tick_fake)
        self._fake_pct = 0.0

        self._build_ui(description)
        self._set_status(self.STATUS_PREVIEW)

    def _build_ui(self, description: str):
        self.setStyleSheet(
            f"QFrame {{ background:{BG_CARD}; border:1px solid {PURPLE}44;"
            f"  border-radius:12px; }}"
        )

        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(16, 14, 16, 14)
        self._lay.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        self._badge = Badge("VORSCHAU", "#2a1a3a", PURPLE)
        name = lbl(f"{self._image}:{self._tag}", TEXT_PRI, 13, bold=True)
        hdr.addWidget(name)
        hdr.addWidget(self._badge)
        hdr.addStretch()
        close = ghost_btn("✕")
        close.setFixedSize(28, 28)
        close.clicked.connect(lambda: self.removed.emit(self.id))
        hdr.addWidget(close)
        self._lay.addLayout(hdr)

        # Description
        if description:
            self._lay.addWidget(lbl(description[:90], TEXT_HINT, 10))

        # Config preview notice
        self._preview_notice = QFrame()
        self._preview_notice.setStyleSheet(
            f"QFrame {{ background:#1a1020; border:1px solid {PURPLE}33;"
            f"  border-radius:6px; }}"
        )
        pn_lay = QHBoxLayout(self._preview_notice)
        pn_lay.setContentsMargins(10, 8, 10, 8)
        pn_lay.addWidget(lbl("⚡", PURPLE, 14))
        pn_lay.addWidget(lbl("Vorgabe-Config im Editor geladen", PURPLE, 11, bold=True))
        pn_lay.addStretch()
        self._lay.addWidget(self._preview_notice)

        # Hint
        self._hint = lbl("Config prüfen — dann Image pullen:", TEXT_HINT, 11)
        self._lay.addWidget(self._hint)

        # Progress bar
        self._bar = PurpleProgressBar()
        self._lay.addWidget(self._bar)

        # Progress label row
        prog_row = QHBoxLayout()
        self._prog_lbl  = lbl("", TEXT_HINT, 10)
        self._prog_pct  = lbl("", PURPLE, 10, bold=True)
        prog_row.addWidget(self._prog_lbl)
        prog_row.addStretch()
        prog_row.addWidget(self._prog_pct)
        self._lay.addLayout(prog_row)

        # Buttons
        self._btn_row = QHBoxLayout()
        self._pull_btn   = mk_btn("⬇  Jetzt pullen", PURPLE, BG_DARK)
        self._reload_btn = ghost_btn("⚡")
        self._reload_btn.setFixedWidth(36)
        self._reload_btn.setToolTip("Config erneut laden")
        self._reload_btn.clicked.connect(lambda: self.load_preset.emit(f"{self._image}:{self._tag}"))
        self._start_btn  = mk_btn("▶  Starten", GREEN, BG_DARK)
        self._pull_btn.clicked.connect(self._start_pull)
        self._start_btn.clicked.connect(lambda: self.done.emit(f"{self._image}:{self._tag}", "start"))
        self._btn_row.addWidget(self._pull_btn)
        self._btn_row.addWidget(self._reload_btn)
        self._btn_row.addStretch()
        self._btn_row.addWidget(self._start_btn)
        self._lay.addLayout(self._btn_row)

    def _set_status(self, status: str):
        self._status = status
        if status == self.STATUS_PREVIEW:
            self._badge.setText("VORSCHAU")
            self._badge.setStyleSheet(f"background:#2a1a3a; color:{PURPLE}; border-radius:4px; padding:2px 8px; font-size:10px; font-weight:600; border:none;")
            self.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {PURPLE}44; border-radius:12px; }}")
            self._preview_notice.show(); self._hint.show()
            self._pull_btn.show(); self._reload_btn.show(); self._start_btn.hide()
            self._bar.set_value(0); self._prog_lbl.setText(""); self._prog_pct.setText("")

        elif status == self.STATUS_PULLING:
            self._badge.setText("PULLING")
            self._badge.setStyleSheet(f"background:#1a1030; color:{PURPLE}; border-radius:4px; padding:2px 8px; font-size:10px; font-weight:600; border:none;")
            self.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {PURPLE}88; border-radius:12px; }}")
            self._preview_notice.hide(); self._hint.hide()
            self._pull_btn.hide(); self._reload_btn.hide(); self._start_btn.hide()
            self._prog_lbl.setText("⬇  Wird gepullt…")
            self._bar.start_shimmer()

        elif status == self.STATUS_DONE:
            self._badge.setText("FERTIG")
            self._badge.setStyleSheet(f"background:#0a2a0a; color:{GREEN}; border-radius:4px; padding:2px 8px; font-size:10px; font-weight:600; border:none;")
            self.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {GREEN}66; border-radius:12px; }}")
            self._bar.stop_shimmer(); self._bar.set_value(100)
            self._prog_lbl.setText("✅  Pull abgeschlossen"); self._prog_pct.setText("100%")
            self._pull_btn.hide(); self._start_btn.show(); self._reload_btn.show()

        elif status == self.STATUS_ERROR:
            self._badge.setText("FEHLER")
            self._badge.setStyleSheet(f"background:#2a0a0a; color:{RED}; border-radius:4px; padding:2px 8px; font-size:10px; font-weight:600; border:none;")
            self.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {RED}66; border-radius:12px; }}")
            self._bar.stop_shimmer()
            self._pull_btn.show(); self._start_btn.hide()

    def _start_pull(self):
        self._set_status(self.STATUS_PULLING)
        self._fake_pct = 0.0
        self._fake_timer.start(200)
        self._worker = PullWorker(self._image, self._tag)
        self._worker.finished.connect(self._on_pull_done)
        self._worker.start()

    def _tick_fake(self):
        # Fake progress up to 92% — real pull finishes it to 100%
        step = 2.0 if self._fake_pct < 30 else (0.8 if self._fake_pct < 70 else 0.2)
        self._fake_pct = min(self._fake_pct + step, 92.0)
        self._bar.set_value(self._fake_pct)
        self._prog_pct.setText(f"{self._fake_pct:.0f}%")

    def _on_pull_done(self, success: bool, error: str):
        self._fake_timer.stop()
        if success:
            self._set_status(self.STATUS_DONE)
            self.done.emit(f"{self._image}:{self._tag}", "done")
        else:
            self._set_status(self.STATUS_ERROR)
            self._prog_lbl.setText(f"❌  {error[:80]}")


# ─── Pull Panel (container for multiple PullCards) ────────────────────────────

class PullPanel(QWidget):
    load_preset = pyqtSignal(str)
    deploy      = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self._cards: dict[str, PullCard] = {}

        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(10)

    def add_image(self, data: dict):
        image = data["name"]
        tag   = "latest"
        if ":" in image:
            image, tag = image.split(":", 1)

        card = PullCard(image, tag, data.get("description", ""))
        card.load_preset.connect(self.load_preset.emit)
        card.done.connect(self._on_done)
        card.removed.connect(self._remove_card)
        self._cards[card.id] = card
        self._lay.addWidget(card)

        # Immediately emit load_preset so editor shows default config
        self.load_preset.emit(f"{image}:{tag}")

    def _remove_card(self, card_id: str):
        if card_id in self._cards:
            c = self._cards.pop(card_id)
            c.deleteLater()

    def _on_done(self, image_tag: str, status: str):
        if status == "start":
            self.deploy.emit(image_tag)