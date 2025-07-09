"""Pointwise engine and helper job classes."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from glacium.models.job import Job, JobStatus
from glacium.managers.template_manager import TemplateManager
from glacium.utils.logging import log, log_call
from .base_engine import BaseEngine
from .engine_factory import EngineFactory

__all__: Iterable[str] = [
    "PointwiseEngine",
    "PointwiseScriptJob",
]


@EngineFactory.register
class PointwiseEngine(BaseEngine):
    """Execute Pointwise TCL scripts."""

    def run_script(self, exe: str, script: Path, work: Path) -> None:
        """Execute ``exe`` with ``script`` inside ``work`` directory."""

        log.info(f"RUN: {exe} {script.name}")
        self.run([exe, str(script)], cwd=work)


class PointwiseScriptJob(Job):
    """Render a Pointwise .glf script and execute it."""

    template: Path
    cfg_key_out: str | None = None
    deps: tuple[str, ...] = ()

    # ------------------------------------------------------------------
    def prepare(self):
        """Render the script template into the Pointwise solver directory."""
        work = self.project.paths.solver_dir("pointwise")
        ctx = self._context()
        dest = work / self.template.with_suffix("")
        TemplateManager().render_to_file(self.template, ctx, dest)
        return dest

    def _context(self) -> dict:
        cfg = self.project.config
        ctx = cfg.extras.copy()

        alias_map = {
            "AIRFOIL": "PWS_AIRFOIL_FILE",
            "PROFILE1": "PWS_PROFILE1",
            "PROFILE2": "PWS_PROFILE2",
            "POLARFILE": "PWS_POLAR_FILE",
            "SUCTIONFILE": "PWS_SUCTION_FILE",
        }
        for alias, key in alias_map.items():
            if key in cfg:
                ctx[alias] = cfg[key]

        if self.cfg_key_out and self.cfg_key_out in cfg:
            ctx["OUTFILE"] = cfg[self.cfg_key_out]

        return ctx

    @log_call
    def execute(self) -> None:  # noqa: D401
        cfg = self.project.config
        paths = self.project.paths
        work = paths.solver_dir("pointwise")

        dest_script = self.prepare()

        exe = cfg.get("POINTWISE_BIN", "pointwise")
        engine = EngineFactory.create("PointwiseEngine")
        # Run inside the solver directory so relative paths resolve correctly
        engine.run_script(exe, dest_script, work)

        if self.cfg_key_out:
            out_name = cfg.get(self.cfg_key_out)
            if not out_name:
                log.error(f"{self.cfg_key_out} nicht in Global-Config definiert!")
                self.status = JobStatus.FAILED
                return
            produced = work / out_name
            cfg[self.cfg_key_out] = str(produced.relative_to(self.project.root))

