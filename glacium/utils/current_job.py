from pathlib import Path

_TOKEN = Path.home() / ".glacium_current_job"


def save(name: str) -> None:
    _TOKEN.write_text(name, encoding="utf-8")


def load() -> str | None:
    return _TOKEN.read_text().strip() if _TOKEN.exists() else None
