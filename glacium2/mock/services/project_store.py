from __future__ import annotations

import json
from pathlib import Path


class ProjectStore:
    def __init__(self) -> None:
        self._path: str | None = None
        self._payload: dict[str, object] = {}

    def open(self, path: str) -> dict[str, object]:
        self._path = path
        project_path = Path(path)

        if not project_path.exists() or not project_path.is_file():
            self._payload = {}
            return dict(self._payload)

        try:
            raw = json.loads(project_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self._payload = {}
            return dict(self._payload)

        self._payload = raw if isinstance(raw, dict) else {}
        return dict(self._payload)

    def path(self) -> str | None:
        return self._path

    def data(self) -> dict[str, object]:
        return dict(self._payload)
