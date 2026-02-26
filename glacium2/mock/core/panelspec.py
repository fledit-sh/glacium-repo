from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt

from .logbus import LogBus
from .panel import Panel


@dataclass(frozen=True)
class PanelSpec:
    id: str
    title: str
    area: Qt.DockWidgetArea
    factory: Callable[[LogBus], Panel]
    dock: bool = True
    workspace: bool = False
