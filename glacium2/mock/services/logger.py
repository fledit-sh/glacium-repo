from __future__ import annotations


class Logger:
    def __init__(self) -> None:
        self._lines: list[str] = []

    def push(self, text: str) -> None:
        self._lines.append(text)

    def lines(self) -> list[str]:
        return list(self._lines)
