from __future__ import annotations


class OpenProjectRouter:
    def __init__(self) -> None:
        self._targets: list[object] = []

    def bind(self, target: object) -> None:
        if hasattr(target, "open"):
            self._targets.append(target)

    def emit(self, path: str) -> None:
        for target in self._targets:
            target.open(path)
