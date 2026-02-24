from __future__ import annotations

from typing import Any, Protocol


class PlotterPort(Protocol):
    @property
    def widget(self) -> Any:
        ...

    def clear(self) -> None:
        ...

    def add(self, dataset: Any, scalar: str | None = None) -> None:
        ...

    def axes(self) -> None:
        ...

    def bar(self, title: str | None = None) -> None:
        ...

    def camera(self, camera_position: Any) -> None:
        ...

    def render(self) -> None:
        ...

    def shot(self, path: str) -> None:
        ...
