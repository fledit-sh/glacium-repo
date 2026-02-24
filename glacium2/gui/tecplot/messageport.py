from __future__ import annotations

from typing import Protocol


class MessagePort(Protocol):
    def error(self, title: str, text: str) -> None:
        ...

    def info(self, title: str, text: str) -> None:
        ...
