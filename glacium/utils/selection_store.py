from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SelectionStore:
    """Simple wrapper to persist and load a selection token."""

    path: Path

    def save(self, value: str) -> None:
        """Write ``value`` to :attr:`path`."""
        self.path.write_text(value, encoding="utf-8")

    def load(self) -> str | None:
        """Return the stored value or ``None`` if :attr:`path` does not exist."""
        return self.path.read_text().strip() if self.path.exists() else None
