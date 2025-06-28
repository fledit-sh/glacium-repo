# glacium/engines/py_engine.py
from pathlib import Path
from typing import Sequence, Callable

class PyEngine:
    """Ausführtbare Python-Callback als Job-Engine."""
    def __init__(self, fn: Callable[[Path, Sequence[str]], None]):
        self.fn = fn

    def run(self, cmd: Sequence[str], cwd: Path, **_) -> None:
        self.fn(cwd, cmd)                 # kein Sub-Prozess
