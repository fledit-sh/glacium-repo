from __future__ import annotations

from .panelspec import PanelSpec


class Registry:
    def __init__(self) -> None:
        self._items: dict[str, PanelSpec] = {}

    def add(self, spec: PanelSpec) -> None:
        self._items[spec.id] = spec

    def items(self) -> dict[str, PanelSpec]:
        return dict(self._items)
