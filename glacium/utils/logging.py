# glacium/utils/logging.py
from __future__ import annotations
from rich.console import Console
from rich.logging import RichHandler
import logging
# Basiskonfiguration – ändert nichts an globalem root‐Logger
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