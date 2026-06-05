"""CachyOS Dashboard — Entry Point."""
import sys
import psutil
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt

from config import APP_NAME, STYLE
from ui.sidebar import Sidebar
from pages.dashboard import DashboardPage
from pages.docker_page import DockerPage
from pages.compose.compose_page import ComposePage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1200, 800)
        self.resize(1440, 900)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._switch)
        root.addWidget(self._sidebar)

        # Pages
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")
        self._stack.addWidget(DashboardPage())
        self._stack.addWidget(DockerPage())
        self._stack.addWidget(ComposePage())
        root.addWidget(self._stack)

    def _switch(self, idx: int):
        self._stack.setCurrentIndex(idx)


def main():
    psutil.cpu_percent(interval=0.1)   # prime the pump
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()