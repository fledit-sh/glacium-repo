from __future__ import annotations

"""Custom Jinja filters used across templates."""

from pathlib import Path
import shlex
from typing import Any

__all__ = ["posix_path", "shell_quote"]


def posix_path(value: str | Path) -> str:
    """Return ``value`` as a POSIX style path string."""
    return str(Path(value).as_posix())


def shell_quote(value: Any) -> str:
    """Return ``value`` safely quoted for shell usage."""
    return shlex.quote(str(value))
