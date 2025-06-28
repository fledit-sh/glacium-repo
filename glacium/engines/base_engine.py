"""Base classes for running external binaries."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Sequence, IO, Optional

from glacium.utils.logging import log


class BaseEngine:
    """Small helper class wrapping subprocess execution."""

    def __init__(self, timeout: int | None = None) -> None:
        """Create engine with optional *timeout* for command execution."""

        self.timeout = timeout

    def run(
        self, cmd: Sequence[str], *, cwd: Path, stdin: Optional[IO[str]] = None
    ) -> None:
        """Execute *cmd* inside *cwd* with optional timeout."""
        subprocess.run(
            cmd,
            stdin=stdin,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=self.timeout,
        )


class XfoilEngine(BaseEngine):
    """Engine wrapper used by :class:`XfoilScriptJob`."""

    def run_script(self, exe: str, script: Path, work: Path) -> None:
        """Execute ``exe`` using ``script`` inside ``work`` directory."""

        log.info(f"🚀  {exe} < {script.name}")
        with script.open("r") as stdin:
            self.run([exe], cwd=work, stdin=stdin)


class DummyEngine(BaseEngine):
    """Engine used for tests; simulates a long running task."""

    def timer(self, seconds: int = 30) -> None:
        """Sleep for the given number of seconds."""
        time.sleep(seconds)

    def run_job(self, name: str, work: Path | None = None) -> None:
        log.info(f"DummyEngine running {name} for 30 seconds")
        self.timer(30)

