# ─── CachyOS Dashboard — Config ──────────────────────────────────────────────

APP_NAME    = "CachyOS Dashboard"
APP_VERSION = "2.0.0"
REFRESH_FAST = 2000   # ms
REFRESH_SLOW = 10000  # ms
REFRESH_DOCKER = 8000 # ms
STACKS_PATH = "/opt/stacks"

# ─── Farben ───────────────────────────────────────────────────────────────────
BG_DARK    = "#0a0a0a"
BG_CARD    = "#111111"
BG_CARD2   = "#161616"
BG_CARD3   = "#1a1a1a"
BORDER     = "#222222"
BORDER_HVR = "#333333"

TEXT_PRI   = "#ffffff"
TEXT_SEC   = "#94a3b8"
TEXT_HINT  = "#475569"

BLUE       = "#89b4fa"
GREEN      = "#a6e3a1"
RED        = "#f38ba8"
ORANGE     = "#fab387"
PURPLE     = "#cba6f7"
TEAL       = "#94e2d5"
YELLOW     = "#f9e2af"

SIDEBAR_W  = 56

# ─── Global Stylesheet ────────────────────────────────────────────────────────
STYLE = f"""
QMainWindow, QWidget {{
    background: {BG_DARK};
    color: {TEXT_PRI};
    font-family: 'Inter', 'Noto Sans', 'Segoe UI', sans-serif;
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: {BG_CARD}; width: 6px; border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: #333; border-radius: 3px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background: {BG_CARD}; height: 6px; border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: #333; border-radius: 3px; min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
QTableWidget {{
    background: {BG_CARD}; border: none;
    gridline-color: {BORDER}; color: {TEXT_PRI}; font-size: 12px;
}}
QTableWidget::item {{
    padding: 6px 8px; border-bottom: 1px solid {BORDER};
}}
QTableWidget::item:selected {{ background: #1e293b; color: {TEXT_PRI}; }}
QHeaderView::section {{
    background: {BG_CARD2}; color: {TEXT_SEC};
    padding: 6px 8px; border: none;
    border-bottom: 1px solid {BORDER};
    font-size: 11px; font-weight: 500;
}}
QLabel {{ background: transparent; }}
QPushButton {{
    border-radius: 6px; padding: 5px 14px;
    font-size: 12px; font-weight: 500; border: none;
    cursor: pointer;
}}
QTextEdit, QPlainTextEdit {{
    background: #0d0d0d; color: {GREEN};
    border: 1px solid {BORDER}; border-radius: 8px;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 12px; padding: 8px;
}}
QLineEdit {{
    background: {BG_CARD2}; color: {TEXT_PRI};
    border: 1px solid {BORDER}; border-radius: 6px;
    padding: 6px 10px; font-size: 12px;
}}
QLineEdit:focus {{
    border: 1px solid {BLUE};
}}
QComboBox {{
    background: {BG_CARD2}; color: {TEXT_PRI};
    border: 1px solid {BORDER}; border-radius: 6px;
    padding: 5px 10px; font-size: 12px;
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background: {BG_CARD2}; color: {TEXT_PRI};
    border: 1px solid {BORDER}; selection-background-color: #1e293b;
}}
QSplitter::handle {{ background: {BORDER}; }}
QToolTip {{
    background: {BG_CARD2}; color: {TEXT_PRI};
    border: 1px solid {BORDER}; border-radius: 4px;
    padding: 4px 8px; font-size: 11px;
}}
"""