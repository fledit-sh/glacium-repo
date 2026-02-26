from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow, QWidget


class DockBuilder:
    def __init__(self, window: QMainWindow) -> None:
        self._window = window

    def add(
        self,
        title: str,
        widget: QWidget,
        area: Qt.DockWidgetArea,
        name: str | None = None,
    ) -> QDockWidget:
        dock = QDockWidget(title, self._window)
        if name:
            dock.setObjectName(name)
        dock.setWidget(widget)
        self._window.addDockWidget(area, dock)
        return dock
