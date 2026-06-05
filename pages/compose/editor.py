"""VS Code–style YAML editor with syntax highlighting and line numbers."""
from __future__ import annotations
import re
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPlainTextEdit, QTextEdit
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QTextCharFormat, QSyntaxHighlighter,
    QTextDocument, QFont, QTextCursor, QTextFormat
)
from config import *


# ─── YAML Syntax Highlighter ──────────────────────────────────────────────────

class YamlHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document)

        def fmt(color: str, bold: bool = False) -> QTextCharFormat:
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            return f

        self._rules = [
            # Comments
            (re.compile(r"#.*$"),                         fmt("#6a737d")),
            # Keys
            (re.compile(r"^(\s*)([a-zA-Z_][\w\-]*)(\s*):"), fmt(BLUE, bold=True)),
            # String values
            (re.compile(r'(?<=:\s)"[^"]*"'),              fmt(GREEN)),
            (re.compile(r"(?<=:\s)'[^']*'"),              fmt(GREEN)),
            # Numbers
            (re.compile(r"(?<=:\s)\b\d+(\.\d+)?\b"),     fmt(ORANGE)),
            # Booleans / null
            (re.compile(r"(?<=:\s)(true|false|null|yes|no)\b"), fmt(PURPLE)),
            # List dashes
            (re.compile(r"^\s*-\s"),                      fmt(TEAL)),
            # Anchors / aliases
            (re.compile(r"&\w+|\*\w+"),                   fmt(YELLOW)),
            # Port mappings like 8080:80
            (re.compile(r"\b\d+:\d+\b"),                  fmt(ORANGE)),
        ]

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                # For the key rule the actual key is group 2
                if pattern.groups >= 2:
                    start = m.start(2)
                    length = len(m.group(2))
                else:
                    start  = m.start()
                    length = m.end() - m.start()
                self.setFormat(start, length, fmt)


# ─── Line Number Area ─────────────────────────────────────────────────────────

class _LineNumberArea(QWidget):
    def __init__(self, editor: "YamlEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)


# ─── YAML Editor ─────────────────────────────────────────────────────────────

class YamlEditor(QPlainTextEdit):
    content_changed = pyqtSignal(str)

    FONT_SIZE    = 13
    LINE_SPACING = 1.4

    def __init__(self, parent=None):
        super().__init__(parent)

        font = QFont("JetBrains Mono, Fira Code, Cascadia Code, Consolas, monospace")
        font.setPointSize(self.FONT_SIZE)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self.setStyleSheet(
            f"QPlainTextEdit {{ background:#0e0e0e; color:{TEXT_PRI};"
            f"  border:none; padding-left:4px; selection-background-color:#264f78; }}"
        )
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self._line_number_area = _LineNumberArea(self)
        self._highlighter = YamlHighlighter(self.document())

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self.textChanged.connect(lambda: self.content_changed.emit(self.toPlainText()))

        self._update_line_number_area_width(0)
        self._highlight_current_line()

    # ── Line numbers ──────────────────────────────────────────────────────────

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event):
        p = QPainter(self._line_number_area)
        p.fillRect(event.rect(), QColor("#0a0a0a"))
        block       = self.firstVisibleBlock()
        block_num   = block.blockNumber()
        top         = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom      = top + round(self.blockBoundingRect(block).height())
        current_num = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                color = QColor(BLUE) if block_num == current_num else QColor(TEXT_HINT)
                p.setPen(color)
                p.setFont(self.font())
                p.drawText(
                    0, top,
                    self._line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_num + 1)
                )
            block     = block.next()
            top       = bottom
            bottom    = top + round(self.blockBoundingRect(block).height())
            block_num += 1

    # ── Current line highlight ────────────────────────────────────────────────

    def _highlight_current_line(self):
        extras: list[QTextEdit.ExtraSelection] = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor("#1a1a2e"))
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extras.append(sel)
        self.setExtraSelections(extras)

    # ── Tab = 2 spaces ────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText("  ")
        else:
            super().keyPressEvent(event)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_content(self, text: str):
        self.setPlainText(text)

    def get_content(self) -> str:
        return self.toPlainText()