from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QMainWindow, QToolBar


class ToolbarBuilder:
    def __init__(self, window: QMainWindow) -> None:
        self._window = window

    def build(self, open_handler: Callable[[], None]) -> QToolBar:
        toolbar = QToolBar("Main", self._window)
        self._window.addToolBar(toolbar)

        open_action = toolbar.addAction("Open Project…")
        open_action.triggered.connect(open_handler)
        return toolbar
