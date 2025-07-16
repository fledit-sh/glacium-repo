"""Shared logging helpers using :mod:`rich` for colourful output.

The global log level can be configured with the ``GLACIUM_LOG_LEVEL``
environment variable which falls back to ``"INFO"`` if unset.
"""

from __future__ import annotations

import logging
import os
import verboselogs
from rich.console import Console
from rich.logging import RichHandler

# Basiskonfiguration – ändert nichts am globalen ``root``‑Logger
_LEVEL = os.getenv("GLACIUM_LOG_LEVEL", "INFO").upper()

verboselogs.install()

console = Console()
handler = RichHandler(console=console, markup=True, show_time=False)
logging.basicConfig(
    level=_LEVEL,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[handler],
)

# Additional log level matching :func:`verboselogs.VerboseLogger.success`.
_SUCCESS_LEVEL = 25
logging.addLevelName(_SUCCESS_LEVEL, "SUCCESS")


def _success(self: logging.Logger, message: str, *args, **kwargs) -> None:
    """Log *message* with level ``SUCCESS``."""

    self.log(_SUCCESS_LEVEL, message, *args, **kwargs)


logging.Logger.success = _success  # type: ignore[attr-defined]

log = logging.getLogger("glacium")
log.setLevel(_LEVEL)


def log_call(fn):
    """Return a wrapper logging calls to ``fn`` at ``log.verbose``."""

    from functools import wraps
    from inspect import signature

    sig = signature(fn)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        arg_str = ", ".join(f"{n}={v!r}" for n, v in bound.arguments.items())
        log.verbose(f"{fn.__qualname__}({arg_str})")
        return fn(*args, **kwargs)

    return wrapper
