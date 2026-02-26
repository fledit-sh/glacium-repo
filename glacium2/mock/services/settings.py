from __future__ import annotations


class Settings:
    def __init__(self, initial: dict[str, object] | None = None) -> None:
        self._data: dict[str, object] = dict(initial or {})

    def get(self, key: str, default: object | None = None) -> object | None:
        return self._data.get(key, default)

    def set(self, key: str, value: object) -> None:
        self._data[key] = value
