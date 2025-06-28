"""Utility to persist the currently selected project UID."""

from pathlib import Path

_TOKEN = Path.home() / ".glacium_current"


def save(uid: str) -> None:
    """Write ``uid`` to the token file."""

    _TOKEN.write_text(uid, encoding="utf-8")


def load() -> str | None:
    """Return the stored UID or ``None`` if no project is selected."""

    return _TOKEN.read_text().strip() if _TOKEN.exists() else None


