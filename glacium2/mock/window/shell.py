from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget


class WindowShell(QMainWindow):
    def __init__(self, title: str = "Glacium") -> None:
        super().__init__()
        self.setWindowTitle(title)
        self._workspace_widget: QWidget | None = None
        self._workspace_title: str | None = None
        self._tabs: QTabWidget | None = None

    def build(self) -> None:
        return

    def add_workspace(self, widget: QWidget, title: str) -> None:
        if self._workspace_widget is None and self._tabs is None:
            self._workspace_widget = widget
            self._workspace_title = title
            self.setCentralWidget(widget)
            return

        if self._tabs is None:
            tabs = QTabWidget()
            tabs.addTab(self._workspace_widget, self._workspace_title or "Workspace")
            self._tabs = tabs
            self.setCentralWidget(tabs)

        self._tabs.addTab(widget, title)
