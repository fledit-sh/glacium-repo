"""Generic base for all XFOIL batch jobs.

Subclasses only define:
    • ``name`` – job identifier
    • ``template`` – Jinja file relative to ``glacium/templates``
    • ``cfg_key_out`` – YAML key holding the output file name
    • ``deps`` – optional tuple of job names

All paths come solely from the global configuration; nothing is hard coded.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from glacium.models.job import Job, JobStatus
from glacium.managers.template_manager import TemplateManager
from glacium.utils.logging import log, log_call
from .base_engine import XfoilEngine
from .engine_factory import EngineFactory

__all__: Iterable[str] = [
    "XfoilScriptJob",
]


class XfoilScriptJob(Job):
    """Abstract base class for an XFOIL script job."""

    template: Path                      # e.g. Path("XFOIL.polars.in.j2")
    cfg_key_out: str | None = None      # YAML key containing the file name
    deps: tuple[str, ...] = ()

    # ------------------------------------------------------------------
    def prepare(self):
        """Render the template into the XFOIL solver directory."""
        work = self.project.paths.solver_dir("xfoil")
        ctx = self._context()
        dest = work / self.template.with_suffix("")
        TemplateManager().render_to_file(self.template, ctx, dest)
        return dest

    # ------------------------------------------------------------------
    def _context(self) -> dict:  # subclasses may override
        """Return template context with full config and convenience aliases.

        ``PWS_`` variables are mirrored as short aliases (``AIRFOIL``,
        ``PROFILE1`` …). For each job an additional ``OUTFILE`` key is
        available so templates can call ``SAVE {{ OUTFILE }}``.
        """

        cfg = self.project.config
        ctx = cfg.extras.copy()

        # -------- convenience aliases ----------------------------------
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

        # short alias for the current output file (if key defined)
        if self.cfg_key_out and self.cfg_key_out in cfg:
            ctx["OUTFILE"] = cfg[self.cfg_key_out]

        return ctx

    # ------------------------------------------------------------------
    @log_call
    def execute(self):  # noqa: D401
        cfg   = self.project.config
        paths = self.project.paths
        work  = paths.solver_dir("xfoil")

        # ----------------------------- 1) prepare script ------------
        dest_script = self.prepare()

        # ----------------------------- 2) run XFOIL ---------------
        exe = cfg.get("XFOIL_BIN", "xfoil.exe")
        engine = EngineFactory.create("XfoilEngine")
        engine.run_script(exe, dest_script, work)

        # ----------------------------- 3) reference result --------
        if self.cfg_key_out:
            out_name = cfg.get(self.cfg_key_out)
            if not out_name:
                log.error(f"{self.cfg_key_out} not defined in global config!")
                self.status = JobStatus.FAILED
                return
            produced = work / out_name
            cfg[self.cfg_key_out] = str(produced.relative_to(self.project.root))
