"""System dashboard page."""
from __future__ import annotations
import psutil
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import QTimer

from config import *
from ui.widgets import lbl, StatCard, UsageBar, SectionCard
from ui.charts  import PerfChart
from core.system_metrics import (
    get_cpu, get_memory, get_gpu, get_uptime,
    get_network_speed, get_disks, get_users,
    get_top_processes, get_firewall, _run
)

# Local imports for sub-cards
from PyQt6.QtWidgets import QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PyQt6.QtGui import QColor


class NetworkCard(SectionCard):
    def __init__(self, parent=None):
        super().__init__("Netzwerk", parent)
        self._prev_rx = self._prev_tx = 0

        self.layout_.addWidget(lbl("", TEXT_SEC, 11))   # iface placeholder
        self._iface = self.layout_.itemAt(1).widget()

        for attr, color, arrow in [("_dl","↓ Download", BLUE), ("_ul","↑ Upload", GREEN)]:
            row = QHBoxLayout()
            row.addWidget(lbl(arrow, color, 12))
            speed = lbl("0.00 Mbit/s", TEXT_PRI, 12, bold=True)
            row.addStretch(); row.addWidget(speed)
            self.layout_.addLayout(row)
            bar   = UsageBar(0, color)
            total = lbl("Gesamt: 0 GB", TEXT_HINT, 10)
            self.layout_.addWidget(bar)
            self.layout_.addWidget(total)
            setattr(self, f"{attr}_lbl",   speed)
            setattr(self, f"{attr}_bar",   bar)
            setattr(self, f"{attr}_total", total)

        self.layout_.addStretch()

    def refresh(self):
        data = get_network_speed(self._prev_rx, self._prev_tx)
        self._iface.setText(f"Interface: {data['iface']}")
        self._dl_lbl.setText(data["dl_str"]); self._ul_lbl.setText(data["ul_str"])
        self._dl_bar.set_value(min(data["dl_mbit"] / 10, 100))
        self._ul_bar.set_value(min(data["ul_mbit"] / 10, 100))
        self._dl_total.setText(f"Gesamt: {data['rx_total']}")
        self._ul_total.setText(f"Gesamt: {data['tx_total']}")
        self._prev_rx = data["rx_bytes"]
        self._prev_tx = data["tx_bytes"]


class FirewallCard(SectionCard):
    def __init__(self, parent=None):
        super().__init__("Firewall", parent)
        sr = QHBoxLayout()
        self._dot    = QLabel("●")
        self._dot.setStyleSheet(f"color:{RED}; font-size:14px; background:transparent; border:none;")
        self._status = lbl("…", RED, 16, bold=True)
        self._type   = lbl("", TEXT_HINT, 11)
        sr.addWidget(self._dot); sr.addWidget(self._status)
        sr.addStretch(); sr.addWidget(self._type)
        self.layout_.addLayout(sr)
        for attr, title in [("_rules", "Regeln"), ("_blocked", "Blockierte Versuche")]:
            r = QHBoxLayout(); r.addWidget(lbl(title, TEXT_SEC, 12)); r.addStretch()
            v = lbl("0", TEXT_PRI, 12, bold=True); setattr(self, attr, v); r.addWidget(v)
            self.layout_.addLayout(r)
        self.layout_.addStretch()

    def refresh(self):
        d = get_firewall()
        if d["active"]:
            for w in [self._dot, self._status]:
                w.setStyleSheet(f"color:{GREEN}; font-size:{'14' if w is self._dot else '16'}px; font-weight:{'400' if w is self._dot else '600'}; background:transparent; border:none;")
            self._status.setText("Aktiv"); self._type.setText(d["type"])
        else:
            for w in [self._dot, self._status]:
                w.setStyleSheet(f"color:{RED}; font-size:{'14' if w is self._dot else '16'}px; font-weight:{'400' if w is self._dot else '600'}; background:transparent; border:none;")
            self._status.setText("Inaktiv"); self._type.setText("none")
        self._rules.setText(str(d["rules"])); self._blocked.setText(str(d["blocked"]))


class UsersCard(SectionCard):
    def __init__(self, parent=None):
        super().__init__("Angemeldete Benutzer", parent)
        self.layout_.addStretch()

    def refresh(self):
        while self.layout_.count() > 2:
            item = self.layout_.takeAt(1)
            if item.widget(): item.widget().deleteLater()
        users = get_users()
        if not users:
            self.layout_.insertWidget(1, lbl("Keine aktiven Sessions", TEXT_SEC, 12))
            return
        for u in users:
            row = QHBoxLayout()
            av  = QLabel(u["name"][0].upper())
            av.setFixedSize(32, 32)
            from PyQt6.QtCore import Qt
            av.setAlignment(Qt.AlignmentFlag.AlignCenter)
            av.setStyleSheet(f"background:#1e3a5f; color:{BLUE}; border-radius:16px; font-weight:600; font-size:13px; border:none;")
            info = QVBoxLayout(); info.setSpacing(1)
            info.addWidget(lbl(u["name"], TEXT_PRI, 12, bold=True))
            info.addWidget(lbl(f"{u['terminal']} · {u['started']}", TEXT_HINT, 10))
            dot = QLabel("●"); dot.setStyleSheet(f"color:{GREEN}; font-size:10px; background:transparent; border:none;")
            row.addWidget(av); row.addLayout(info); row.addStretch(); row.addWidget(dot)
            w = QWidget(); w.setStyleSheet("background:transparent;"); w.setLayout(row)
            self.layout_.insertWidget(self.layout_.count() - 1, w)


class DiskCard(SectionCard):
    def __init__(self, parent=None):
        super().__init__("Festplatten", parent)

    def refresh(self):
        while self.layout_.count() > 1:
            item = self.layout_.takeAt(1)
            if item.widget(): item.widget().deleteLater()
        for d in get_disks():
            pct   = d["percent"]
            color = RED if pct > 90 else ORANGE if pct > 75 else BLUE
            w  = QWidget(); w.setStyleSheet("background:transparent;")
            wl = QVBoxLayout(w); wl.setContentsMargins(0, 0, 0, 0); wl.setSpacing(4)
            top = QHBoxLayout()
            top.addWidget(lbl(d["mount"], TEXT_SEC, 12))
            top.addStretch()
            top.addWidget(lbl(f"{d['used']} / {d['total']}", TEXT_SEC, 11))
            wl.addLayout(top)
            wl.addWidget(UsageBar(pct, color))
            wl.addWidget(lbl(f"{d['free']} frei · {pct:.0f}%", TEXT_HINT, 10))
            self.layout_.addWidget(w)


class ProcessTable(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER}; border-radius:12px; }}")
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(10)
        from ui.widgets import section_label
        lay.addWidget(section_label("Top Prozesse (nach CPU)"))
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["PID", "Benutzer", "Prozess", "CPU %", "MEM %"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for i in [0, 1, 3, 4]:
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().hide(); self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(280)
        lay.addWidget(self.table)

    def refresh(self):
        procs = get_top_processes(12)
        self.table.setRowCount(len(procs))
        for row, p in enumerate(procs):
            cpu = p["cpu"]; mem = p["mem"]
            for col, (text, color) in enumerate([
                (p["pid"],  TEXT_HINT),
                (p["user"], TEXT_SEC),
                (p["name"], TEXT_PRI),
                (f"{cpu:.1f}", RED if cpu > 50 else ORANGE if cpu > 20 else GREEN),
                (f"{mem:.1f}", TEXT_SEC),
            ]):
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                self.table.setItem(row, col, item)
        self.table.resizeRowsToContents()


# ─── Dashboard Page ───────────────────────────────────────────────────────────

class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        tux = QLabel("🐧"); tux.setStyleSheet("font-size:28px; background:transparent; border:none;")
        hdr.addWidget(tux)
        hdr.addWidget(lbl("Linux System Overview", TEXT_PRI, 22, bold=True))
        hdr.addStretch()
        self._update_lbl = lbl("", TEXT_HINT, 11)
        hdr.addWidget(self._update_lbl)
        lay.addLayout(hdr)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(from_PyQt6 := __import__('PyQt6.QtCore', fromlist=['Qt']).Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        content = QWidget(); content.setStyleSheet("background:transparent;")
        clay = QVBoxLayout(content); clay.setSpacing(16); clay.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(content)
        lay.addWidget(scroll)

        # Stat cards
        self._cpu = StatCard("CPU Load", "–")
        self._ram = StatCard("Memory",   "–")
        self._gpu = StatCard("GPU Temp", "N/A", "Not found")
        self._upt = StatCard("Uptime",   "–",  "System stable")
        sr = QHBoxLayout()
        for c in [self._cpu, self._ram, self._gpu, self._upt]: sr.addWidget(c)
        clay.addLayout(sr)

        # Chart + Network
        cr = QHBoxLayout()
        self._chart = PerfChart()
        self._chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        cr.addWidget(self._chart, 2)
        self._net = NetworkCard(); self._net.setFixedWidth(280)
        cr.addWidget(self._net, 1)
        clay.addLayout(cr)

        # Mid row
        mr = QHBoxLayout()
        self._fw    = FirewallCard(); self._fw.setMinimumHeight(180)
        self._users = UsersCard();    self._users.setMinimumHeight(180)
        self._disk  = DiskCard();     self._disk.setMinimumHeight(180)
        for w in [self._fw, self._users, self._disk]: mr.addWidget(w)
        clay.addLayout(mr)

        # Processes
        self._procs = ProcessTable()
        clay.addWidget(self._procs)

        # Timers
        psutil.cpu_percent(interval=0.1)
        self._t_fast = QTimer(); self._t_fast.timeout.connect(self._tick_fast); self._t_fast.start(REFRESH_FAST)
        self._t_slow = QTimer(); self._t_slow.timeout.connect(self._tick_slow); self._t_slow.start(REFRESH_SLOW)
        self._tick_fast(); self._tick_slow()

    def _tick_fast(self):
        cpu = get_cpu(); mem = get_memory()
        self._cpu.update_value(cpu["usage_str"], cpu["freq"], cpu["usage"] > 90)
        self._ram.update_value(mem["used"], f"{mem['total']} total · {mem['percent']:.0f}%", mem["percent"] > 90)
        self._chart.push(cpu["usage"], mem["percent"])
        self._net.refresh()
        self._update_lbl.setText(f"Aktualisiert: {datetime.now().strftime('%H:%M:%S')}")

    def _tick_slow(self):
        upt = get_uptime(); self._upt.update_value(upt["str"], "System stable")
        gpu = get_gpu();    self._gpu.update_value(gpu["temp"], gpu["name"], gpu["temp"] not in ("N/A",) and int(gpu["temp"].rstrip("°C") or 0) > 85)
        self._fw.refresh(); self._users.refresh(); self._disk.refresh(); self._procs.refresh()