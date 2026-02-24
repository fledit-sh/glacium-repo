from __future__ import annotations

from typing import Protocol


class DialogPort(Protocol):
    def open(self) -> str:
        ...

    def save(self) -> str:
        ...
