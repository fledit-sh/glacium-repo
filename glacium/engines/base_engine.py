"""Engine implementations wrapping external solver calls."""
from __future__ import annotations

from pathlib import Path

from glacium.core.base import EngineBase
from glacium.utils.logging import log


class BaseEngine(EngineBase):
    """Small helper class wrapping subprocess execution."""

    pass


class XfoilEngine(BaseEngine):
    """Engine wrapper used by :class:`XfoilScriptJob`."""

    def __init__(self, exe: str, timeout: int | None = None) -> None:
        super().__init__(timeout)
        self.exe = exe

    def run_script(self, script: Path, work: Path) -> None:
        """Execute ``self.exe`` using ``script`` inside ``work`` directory."""

        log.info(f"RUN: {self.exe} < {script.name}")
        with script.open("r") as stdin:
            self.run([self.exe], cwd=work, stdin=stdin)


class DummyEngine(BaseEngine):
    """Engine used for tests; simulates a long running task."""

    def timer(self, seconds: int = 30) -> None:
        """Sleep for the given number of seconds."""
        import time

        time.sleep(seconds)

    def run_job(self, name: str, work: Path | None = None) -> None:
        log.info(f"DummyEngine running {name} for 30 seconds")
        self.timer(30)
