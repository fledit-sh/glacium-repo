from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Protocol

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt


class LogBus(QObject):
    message = Signal(str)


class Panel(QWidget):
    """
    Base class for detachable panels. Keep it simple:
    - build_ui() in __init__
    - use log_bus.message.emit("...") instead of print
    """
    panel_id: str = "panel.base"
    title: str = "Panel"
    default_dock_area: Qt.DockWidgetArea = Qt.RightDockWidgetArea
    is_dock: bool = True  # False => central tab

    def __init__(self, log_bus: LogBus, parent=None) -> None:
        super().__init__(parent)
        self._log_bus = log_bus

    def log(self, msg: str) -> None:
        self._log_bus.message.emit(f"[{self.panel_id}] {msg}")

    def on_project_opened(self, project_path: str) -> None:
        # optional hook
        pass


@dataclass(frozen=True)
class PanelSpec:
    factory: Callable[[LogBus], Panel]
    panel_id: str
    title: str
    is_dock: bool
    default_dock_area: Qt.DockWidgetArea


class PanelRegistry:
    def __init__(self) -> None:
        self._specs: Dict[str, PanelSpec] = {}

    def register(self, factory: Callable[[LogBus], Panel]) -> None:
        tmp = factory(LogBus())  # cheap instantiate for metadata
        spec = PanelSpec(
            factory=factory,
            panel_id=tmp.panel_id,
            title=tmp.title,
            is_dock=tmp.is_dock,
            default_dock_area=tmp.default_dock_area,
        )
        self._specs[spec.panel_id] = spec

    def specs(self) -> Dict[str, PanelSpec]:
        return dict(self._specs)