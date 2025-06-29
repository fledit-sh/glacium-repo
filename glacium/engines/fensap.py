"""Support for running FENSAP via templated shell scripts."""

from __future__ import annotations

import yaml
from pathlib import Path

from glacium.models.job import Job
from glacium.managers.TemplateManager import TemplateManager
from glacium.utils.logging import log
from .base_engine import BaseEngine


class FensapEngine(BaseEngine):
    """Execute ``.solvercmd`` files via ``nti_sh.exe``."""

    def run_script(self, exe: str, script: Path, work: Path) -> None:
        """Run ``script`` using ``exe`` inside ``work`` directory."""

        log.info(f"🚀  {exe} {script.name}")
        self.run([exe, str(script)], cwd=work)


class FensapRunJob(Job):
    """Render FENSAP input files and launch the solver."""

    name = "FENSAP_RUN"
    deps: tuple[str, ...] = ()

    _DEFAULT_EXE = (
        r"C:\\Program Files\\ANSYS Inc\\v251\\fensapice\\bin\\nti_sh.exe"
    )

    def execute(self) -> None:  # noqa: D401
        cfg = self.project.config
        paths = self.project.paths
        work = paths.solver_dir("run_FENSAP")

        defaults_file = Path(__file__).resolve().parents[1] / "config" / "defaults" / "global_default.yaml"
        defaults = yaml.safe_load(defaults_file.read_text()) if defaults_file.exists() else {}

        ctx = {**defaults, **cfg.extras}

        tm = TemplateManager()
        tm.render_to_file("FENSAP.FENSAP.files.j2", ctx, work / "files")
        tm.render_to_file("FENSAP.FENSAP.par.j2", ctx, work / "fensap.par")
        tm.render_to_file("FENSAP.solvercmd.j2", ctx, work / ".solvercmd")

        exe = cfg.get("FENSAP_EXE", self._DEFAULT_EXE)
        engine = FensapEngine()
        engine.run_script(exe, work / ".solvercmd", work)


