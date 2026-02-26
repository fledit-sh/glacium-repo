from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from .logbus import LogBus


class Panel(QWidget):
    panel_id: str = "panel.base"
    title: str = "Panel"
    default_dock_area: Qt.DockWidgetArea = Qt.RightDockWidgetArea
    is_dock: bool = True

    def __init__(self, log_bus: LogBus, parent=None) -> None:
        super().__init__(parent)
        self._log_bus = log_bus

    def log(self, msg: str) -> None:
        self._log_bus.message.emit(f"[{self.panel_id}] {msg}")

    def open(self, project_path: str) -> None:
        _ = project_path
