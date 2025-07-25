# glacium/engines/py_engine.py
from pathlib import Path
from typing import Sequence, Callable

from glacium.core.base import EngineBase

class PyEngine(EngineBase):
    """Execute a Python callable as job engine."""

    def __init__(self, fn: Callable[[Path, Sequence[str]], None], timeout: int | None = None) -> None:
        super().__init__(timeout)
        self.fn = fn

    def run(self, cmd: Sequence[str], *, cwd: Path, stdin=None) -> None:  # type: ignore[override]
        self.fn(cwd, list(cmd))  # no subprocess

    def run_script(self, script: Path, work: Path) -> None:  # pragma: no cover - not used
        with script.open("r") as fh:
            args = [line.strip() for line in fh if line.strip()]
        self.run(args, cwd=work)
