from __future__ import annotations

from typing import Callable

from .logbus import LogBus
from .panel import Panel
from .panelspec import PanelSpec


class Registry:
    def __init__(self) -> None:
        self._items: dict[str, PanelSpec] = {}

    def add(self, factory: Callable[[LogBus], Panel]) -> None:
        panel = factory(LogBus())
        spec = PanelSpec(
            factory=factory,
            panel_id=panel.panel_id,
            title=panel.title,
            is_dock=panel.is_dock,
            default_dock_area=panel.default_dock_area,
        )
        self._items[spec.panel_id] = spec

    def items(self) -> dict[str, PanelSpec]:
        return dict(self._items)
