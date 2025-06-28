"""Shared logging helpers using :mod:`rich` for colourful output."""

from __future__ import annotations

import logging
from rich.console import Console
from rich.logging import RichHandler

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
