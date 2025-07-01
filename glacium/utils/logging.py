"""Shared logging helpers using :mod:`rich` for colourful output."""

from __future__ import annotations

import logging
from functools import wraps
from rich.console import Console
from rich.logging import RichHandler

# Add ``SUCCESS`` level similar to :mod:`verboselogs`
SUCCESS = 35
logging.addLevelName(SUCCESS, "SUCCESS")

# ``TRACE`` level for very fine grained output
TRACE = 5
logging.addLevelName(TRACE, "TRACE")


def _success(self, message: str, *args, **kwargs) -> None:  # type: ignore[override]
    if self.isEnabledFor(SUCCESS):
        self._log(SUCCESS, message, args, **kwargs)


def _trace(self, message: str, *args, **kwargs) -> None:  # type: ignore[override]
    if self.isEnabledFor(TRACE):
        self._log(TRACE, message, args, **kwargs)


logging.Logger.success = _success  # type: ignore[attr-defined]
logging.Logger.trace = _trace  # type: ignore[attr-defined]

# Basiskonfiguration – ändert nichts am globalen ``root``‑Logger
_LEVEL = "INFO"

console = Console()
handler = RichHandler(console=console, markup=True, show_time=False)
logging.basicConfig(
    level=_LEVEL,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[handler],
)

log = logging.getLogger("glacium")
log.setLevel(_LEVEL)


def trace_calls(func):
    """Log entering and exiting of ``func`` at ``TRACE`` level."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        log.log(TRACE, f"\u2192 {func.__qualname__}(...)")  # '→'
        try:
            return func(*args, **kwargs)
        finally:
            log.log(TRACE, f"\u2190 {func.__qualname__}(...)")  # '←'

    return wrapper


__all__ = ["log", "SUCCESS", "TRACE", "trace_calls"]
