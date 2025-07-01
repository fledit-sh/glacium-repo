"""Shared logging helpers using :mod:`rich` for colourful output."""

from __future__ import annotations

import logging
from rich.console import Console
from rich.logging import RichHandler

# Add ``SUCCESS`` level similar to :mod:`verboselogs`
SUCCESS = 35
logging.addLevelName(SUCCESS, "SUCCESS")


def _success(self, message: str, *args, **kwargs) -> None:  # type: ignore[override]
    if self.isEnabledFor(SUCCESS):
        self._log(SUCCESS, message, args, **kwargs)


logging.Logger.success = _success  # type: ignore[attr-defined]

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
