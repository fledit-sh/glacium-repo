from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from ..services import Logger, ProjectStore, Settings
from .logbus import LogBus


class Panel(QWidget):
    panel_id: str = "panel.base"
    title: str = "Panel"
    default_dock_area: Qt.DockWidgetArea = Qt.RightDockWidgetArea
    is_dock: bool = True

    def __init__(
        self,
        log_bus: LogBus,
        logger: Logger,
        settings: Settings,
        project_store: ProjectStore,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._log_bus = log_bus
        self._logger = logger
        self._settings = settings
        self._project_store = project_store

    def log(self, msg: str) -> None:
        text = f"[{self.panel_id}] {msg}"
        self._logger.push(text)
        self._log_bus.message.emit(text)

    def open(self, project_path: str) -> None:
        _ = project_path
