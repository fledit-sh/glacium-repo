"""Support for running FENSAP via templated shell scripts."""

from __future__ import annotations

from pathlib import Path

from glacium.utils.logging import log
from .base_engine import BaseEngine


class FensapEngine(BaseEngine):
    """Execute ``.solvercmd`` files via ``nti_sh.exe``."""

    def run_script(self, exe: str, script: Path, work: Path) -> None:
        """Run ``script`` using ``exe`` inside ``work`` directory."""

        log.info(f"🚀  {exe} {script.name}")
        self.run([exe, str(script)], cwd=work)



