from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt

from .logbus import LogBus
from .panel import Panel


@dataclass(frozen=True)
class PanelSpec:
    factory: Callable[[LogBus], Panel]
    panel_id: str
    title: str
    is_dock: bool
    default_dock_area: Qt.DockWidgetArea
