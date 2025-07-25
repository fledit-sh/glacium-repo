"""Job converting Fluent case files for FENSAP."""

from __future__ import annotations

from pathlib import Path

from glacium.core.base import EngineBase
from glacium.utils.logging import log
from .engine_factory import EngineFactory

__all__ = ["Fluent2FensapEngine"]


@EngineFactory.register
class Fluent2FensapEngine(EngineBase):
    """Run the ``fluent2fensap`` converter."""

    def __init__(self, exe: str, timeout: int | None = None) -> None:
        super().__init__(timeout)
        self.exe = exe

    def convert(self, cas_name: str, cas_stem: str, work: Path) -> None:
        self.run([self.exe, cas_name, cas_stem], cwd=work)


