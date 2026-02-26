from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget


class WindowShell(QMainWindow):
    def __init__(self, title: str = "Glacium") -> None:
        super().__init__()
        self.setWindowTitle(title)
        self._tabs = QTabWidget()

    def build(self) -> None:
        self.setCentralWidget(self._tabs)

    def add(self, widget, title: str) -> None:
        self._tabs.addTab(widget, title)
