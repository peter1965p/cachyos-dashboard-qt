"""Compose Manager page."""
from __future__ import annotations
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QSplitter, QScrollArea, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from config import *
from ui.widgets import lbl, mk_btn, ghost_btn, section_label, Badge, UsageBar
from ui.dialogs import LogDialog
from pages.compose.hub_search import HubSearchWidget
from pages.compose.pull_widget import PullPanel
from pages.compose.editor import YamlEditor
import core.docker_client as dc


# ─── Default Configs ──────────────────────────────────────────────────────────

_DEFAULTS: dict[str, str] = {
    "nginx": """services:
  nginx:
    image: nginx:latest
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./html:/usr/share/nginx/html:ro
networks: {}
""",
    "redis": """services:
  redis:
    image: redis:alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    command: redis-server --save 60 1 --loglevel warning
    volumes:
      - redis_data:/data
volumes:
  redis_data:
networks: {}
""",
    "postgres": """services:
  postgres:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_PASSWORD: changeme
      POSTGRES_USER: postgres
      POSTGRES_DB: app
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
volumes:
  pg_data:
networks: {}
""",
    "mysql": """services:
  mysql:
    image: mysql:8
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: changeme
      MYSQL_DATABASE: app
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
volumes:
  mysql_data:
networks: {}
""",
    "grafana": """services:
  grafana:
    image: grafana/grafana:latest
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
volumes:
  grafana_data:
networks: {}
""",
    "traefik": """services:
  traefik:
    image: traefik:v3.0
    restart: unless-stopped
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
networks: {}
""",
    "portainer": """services:
  portainer:
    image: portainer/portainer-ce:latest
    restart: unless-stopped
    ports:
      - "9000:9000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
volumes:
  portainer_data:
networks: {}
""",
    "mariadb": """services:
  mariadb:
    image: mariadb:11
    restart: unless-stopped
    environment:
      MARIADB_ROOT_PASSWORD: changeme
      MARIADB_DATABASE: app
    ports:
      - "3306:3306"
    volumes:
      - mariadb_data:/var/lib/mysql
volumes:
  mariadb_data:
networks: {}
""",
}

_DEFAULT_TEMPLATE = """services:
  {name}:
    image: {image}
    restart: unless-stopped
networks: {{}}
"""



def get_default_config(image_tag: str) -> str:
    key = image_tag.split("/")[-1].split(":")[0].lower()
    return _DEFAULTS.get(key, _DEFAULT_TEMPLATE.format(name=key, image=image_tag))


# ─── Stack Item in Sidebar ────────────────────────────────────────────────────

class StackItem(QFrame):
    clicked = pyqtSignal(str)   # stack name

    def __init__(self, name: str, active: bool = False, parent=None):
        super().__init__(parent)
        self.name = name
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QFrame {{ background:transparent; border:none;"
            f"  border-radius:6px; padding:2px; }}"
            f"QFrame:hover {{ background:{BG_CARD2}; }}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        bg  = "#0a2a0a" if active else "#2a2a2a"
        fg  = GREEN     if active else TEXT_HINT
        txt = "aktiv"   if active else "inaktiv"
        badge = Badge(txt, bg, fg)
        badge.setFixedWidth(52)
        lay.addWidget(badge)
        lay.addWidget(lbl(name, TEXT_PRI, 12))
        lay.addStretch()

    def mousePressEvent(self, _):
        self.clicked.emit(self.name)


# ─── Left Panel ───────────────────────────────────────────────────────────────

class _LeftPanel(QWidget):
    stack_selected  = pyqtSignal(str)
    deploy_clicked  = pyqtSignal()
    save_clicked    = pyqtSignal()
    stop_clicked    = pyqtSignal()
    restart_clicked = pyqtSignal()
    pull_clicked    = pyqtSignal()
    logs_clicked    = pyqtSignal()
    image_selected  = pyqtSignal(dict)
    new_stack       = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(350)
        self.setMaximumWidth(600)
        self.setStyleSheet(
            f"background:{BG_CARD}; border-right:1px solid {BORDER};"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top: Title + Action Buttons ───────────────────────────────────────
        top = QWidget()
        top.setStyleSheet(f"background:{BG_CARD}; border-bottom:1px solid {BORDER};")
        top_lay = QVBoxLayout(top)
        top_lay.setContentsMargins(20, 16, 20, 12)
        top_lay.setSpacing(12)

        top_lay.addWidget(lbl("Compose", TEXT_PRI, 22, bold=True))

        # Action buttons row
        btn_row = QHBoxLayout()
        self._deploy_btn  = mk_btn("🚀 Deployen", BLUE, BG_DARK)
        self._save_btn    = ghost_btn("💾 Speichern")
        self._more_btn    = ghost_btn("▾")
        self._more_btn.setFixedWidth(32)
        self._more_btn.clicked.connect(self._show_more_menu)
        self._deploy_btn.clicked.connect(self.deploy_clicked.emit)
        self._save_btn.clicked.connect(self.save_clicked.emit)
        btn_row.addWidget(self._deploy_btn)
        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._more_btn)
        btn_row.addStretch()
        top_lay.addLayout(btn_row)
        root.addWidget(top)

        # ── Scrollable content ────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        content = QWidget(); content.setStyleSheet("background:transparent;")
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(20, 16, 20, 16)
        self._content_lay.setSpacing(20)
        scroll.setWidget(content)
        root.addWidget(scroll)

        # Allgemein
        self._content_lay.addWidget(section_label("Allgemein"))
        self._stack_name = QLineEdit()
        self._stack_name.setPlaceholderText("Stack-Name…")
        self._content_lay.addWidget(self._stack_name)
        hint = lbl("Nur Kleinbuchstaben", TEXT_HINT, 10)
        self._content_lay.addWidget(hint)

        # Container / Hub Search
        self._content_lay.addWidget(section_label("Container suchen"))
        self._hub = HubSearchWidget()
        self._hub.image_selected.connect(self.image_selected.emit)
        self._content_lay.addWidget(self._hub)

        # Pull panel
        self._pull_panel = PullPanel()
        self._content_lay.addWidget(self._pull_panel)

        # Stack Liste
        self._content_lay.addWidget(section_label("Stacks"))
        self._stack_list_lay = QVBoxLayout()
        self._stack_list_lay.setSpacing(2)
        self._content_lay.addLayout(self._stack_list_lay)

        self._content_lay.addStretch()

        # Status
        self._status = lbl("", TEXT_HINT, 11)
        self._content_lay.addWidget(self._status)

    def set_status(self, msg: str): self._status.setText(msg)

    def get_stack_name(self) -> str:
        return self._stack_name.text().strip().lower()

    def set_stack_name(self, name: str):
        self._stack_name.setText(name)

    def get_pull_panel(self) -> PullPanel:
        return self._pull_panel

    def populate_stacks(self, stacks: list[dict]):
        while self._stack_list_lay.count():
            item = self._stack_list_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for s in stacks:
            item = StackItem(s["name"], s.get("active", False))
            item.clicked.connect(self.stack_selected.emit)
            self._stack_list_lay.addWidget(item)

    def _show_more_menu(self):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background:{BG_CARD2}; color:{TEXT_PRI};"
            f"  border:1px solid {BORDER}; border-radius:8px; padding:4px; }}"
            f"QMenu::item {{ padding:8px 20px; font-size:12px; }}"
            f"QMenu::item:selected {{ background:#1e293b; border-radius:4px; }}"
        )
        menu.addAction("⏹  Stoppen",    self.stop_clicked.emit)
        menu.addAction("🔄  Neustarten", self.restart_clicked.emit)
        menu.addAction("⬇  Pull",       self.pull_clicked.emit)
        menu.addAction("📋  Logs",       self.logs_clicked.emit)
        menu.exec(self._more_btn.mapToGlobal(self._more_btn.rect().bottomLeft()))


# ─── Right Panel: Editor + .env ───────────────────────────────────────────────

class _RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:#0e0e0e;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Tabs
        tabs = QHBoxLayout()
        tabs.setContentsMargins(0, 0, 0, 0)
        tabs.setSpacing(0)
        self._tabs_bar = QWidget()
        self._tabs_bar.setStyleSheet(
            f"background:{BG_CARD}; border-bottom:1px solid {BORDER};"
        )
        tb_lay = QHBoxLayout(self._tabs_bar)
        tb_lay.setContentsMargins(8, 0, 8, 0)
        tb_lay.setSpacing(0)

        self._tab_compose = self._make_tab("docker-compose.yml", True)
        self._tab_env     = self._make_tab(".env", False)
        tb_lay.addWidget(self._tab_compose)
        tb_lay.addWidget(self._tab_env)
        tb_lay.addStretch()
        lay.addWidget(self._tabs_bar)

        # Editors
        self._compose_editor = YamlEditor()
        self._env_editor     = YamlEditor()
        self._env_editor.hide()
        lay.addWidget(self._compose_editor)
        lay.addWidget(self._env_editor)

        self._tab_compose.clicked.connect(lambda: self._switch_tab(0))
        self._tab_env.clicked.connect(lambda: self._switch_tab(1))
        self._current_tab = 0

    def _make_tab(self, name: str, active: bool) -> QPushButton:
        from PyQt6.QtWidgets import QPushButton
        b = QPushButton(name)
        self._apply_tab_style(b, active)
        return b

    def _apply_tab_style(self, btn, active: bool):
        border = f"border-bottom:2px solid {BLUE};" if active else "border-bottom:2px solid transparent;"
        col    = TEXT_PRI if active else TEXT_HINT
        btn.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{col};"
            f"  {border} border-left:none; border-right:none; border-top:none;"
            f"  padding:10px 16px; font-size:12px; }}"
            f"QPushButton:hover {{ color:{TEXT_PRI}; }}"
        )

    def _switch_tab(self, idx: int):
        self._current_tab = idx
        self._apply_tab_style(self._tab_compose, idx == 0)
        self._apply_tab_style(self._tab_env,     idx == 1)
        self._compose_editor.setVisible(idx == 0)
        self._env_editor.setVisible(idx == 1)

    def get_compose(self) -> str:  return self._compose_editor.get_content()
    def get_env(self)     -> str:  return self._env_editor.get_content()
    def set_compose(self, t: str): self._compose_editor.set_content(t)
    def set_env(self, t: str):     self._env_editor.set_content(t)


# ─── Compose Page ─────────────────────────────────────────────────────────────

class ComposePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_stack_path: str | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._left  = _LeftPanel()
        self._right = _RightPanel()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background:#222;
                width:6px;
            }
            QSplitter::handle:hover {
                background:#444;
            }
        """)
        splitter.addWidget(self._left)
        splitter.addWidget(self._right)
        splitter.setSizes([380, 9999])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        root.addWidget(splitter)

        # Wire signals
        self._left.deploy_clicked.connect(self._deploy)
        self._left.save_clicked.connect(self._save)
        self._left.stop_clicked.connect(self._stop)
        self._left.restart_clicked.connect(self._restart)
        self._left.pull_clicked.connect(self._pull)
        self._left.logs_clicked.connect(self._logs)
        self._left.stack_selected.connect(self._load_stack)
        self._left.image_selected.connect(self._on_image_selected)
        self._left.get_pull_panel().load_preset.connect(self._load_preset)
        self._left.get_pull_panel().deploy.connect(self._on_pull_deploy)

        # Initial stack list
        self._refresh_stacks()

    # ── Stack list ────────────────────────────────────────────────────────────

    def _refresh_stacks(self):
        stacks = dc.list_stacks(STACKS_PATH)
        self._left.populate_stacks(stacks)

    # ── Load stack from sidebar ───────────────────────────────────────────────

    def _load_stack(self, name: str):
        path = os.path.join(STACKS_PATH, name)
        self._current_stack_path = path
        self._left.set_stack_name(name)
        content = dc.read_compose(path)
        if content:
            self._right.set_compose(content)
        env_path = os.path.join(path, ".env")
        if os.path.isfile(env_path):
            with open(env_path) as f:
                self._right.set_env(f.read())
        self._left.set_status(f"Stack '{name}' geladen")

    # ── Hub image selected ────────────────────────────────────────────────────

    def _on_image_selected(self, data: dict):
        self._left.get_pull_panel().add_image(data)

    def _load_preset(self, image_tag: str):
        cfg = get_default_config(image_tag)
        self._right.set_compose(cfg)
        name = image_tag.split("/")[-1].split(":")[0].lower()
        self._left.set_stack_name(name)
        self._left.set_status(f"Vorgabe-Config für '{name}' geladen")

    def _on_pull_deploy(self, image_tag: str):
        self._load_preset(image_tag)
        self._deploy()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _get_path(self) -> str | None:
        name = self._left.get_stack_name()
        if not name:
            self._left.set_status("⚠  Bitte Stack-Namen eingeben")
            return None
        return os.path.join(STACKS_PATH, name)

    def _save(self):
        path = self._get_path()
        if not path: return
        dc.write_compose(path, self._right.get_compose())
        self._current_stack_path = path
        self._left.set_status("✅  Gespeichert")
        self._refresh_stacks()

    def _deploy(self):
        self._save()
        path = self._current_stack_path
        if not path: return
        self._left.set_status("🚀  Deploying…")
        rc, out = dc.compose_up(path)
        self._left.set_status("✅  Deployed!" if rc == 0 else f"❌  Fehler (rc={rc})")
        if out.strip():
            LogDialog("Deploy Output", out, self).exec()
        self._refresh_stacks()

    def _stop(self):
        path = self._current_stack_path
        if not path: return
        self._left.set_status("⏹  Stoppe…")
        rc, out = dc.compose_down(path)
        self._left.set_status("✅  Gestoppt" if rc == 0 else f"❌  Fehler (rc={rc})")
        self._refresh_stacks()

    def _restart(self):
        path = self._current_stack_path
        if not path: return
        self._left.set_status("🔄  Neustarte…")
        rc, out = dc.compose_restart(path)
        self._left.set_status("✅  Neugestartet" if rc == 0 else f"❌  Fehler (rc={rc})")

    def _pull(self):
        path = self._current_stack_path
        if not path: return
        self._left.set_status("⬇  Pulle Images…")
        rc, out = dc.compose_pull(path)
        self._left.set_status("✅  Pull fertig" if rc == 0 else f"❌  Fehler (rc={rc})")

    def _logs(self):
        path = self._current_stack_path
        if not path: return
        _, out = dc.compose_logs(path)
        LogDialog(self._left.get_stack_name() or "Logs", out, self).exec()