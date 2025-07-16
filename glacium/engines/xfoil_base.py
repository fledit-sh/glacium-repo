"""Generisches Grundgerüst für *alle* XFOIL-Batch-Jobs.

Subklassen definieren nur noch:
    • name           – Job-Identifier
    • template       – Jinja-Datei (relativ zu glacium/templates)
    • cfg_key_out    – YAML-Schlüssel, der den *Zieldatei­namen* enthält
    • deps           – optionale Tuple[Jobname]

Alle Pfade kommen **ausschließlich** aus der Global-Config – nichts mehr
hard-gecoded.
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
    """Abstrakte Basisklasse für einen XFOIL-Skript-Job."""

    template: Path                      # z. B. Path("XFOIL.polars.in.j2")
    cfg_key_out: str | None = None      # YAML-Key, der den Dateinamen enthält
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
    def _context(self) -> dict:  # Subklassen können überschreiben
        """Template‑Kontext = komplette Global‑Config **plus** Alias‑Keys.

        • PWS_‑Variablen werden als kurze Aliase (AIRFOIL, PROFILE1 …) gespiegelt.
        • Für jeden Job steht zusätzlich `OUTFILE` zur Verfügung,
          sodass Templates z. B. `SAVE {{ OUTFILE }}` nutzen können.
        """

        cfg = self.project.config
        ctx = cfg.extras.copy()

        # -------- Convenience‑Aliase ----------------------------------
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

        # Kürzel für das aktuelle Ziel‑File (wenn Key definiert)
        if self.cfg_key_out and self.cfg_key_out in cfg:
            ctx["OUTFILE"] = cfg[self.cfg_key_out]

        return ctx

    # ------------------------------------------------------------------
    @log_call
    def execute(self):  # noqa: D401
        cfg   = self.project.config
        paths = self.project.paths
        work  = paths.solver_dir("xfoil")

        # ----------------------------- 1) Skript vorbereiten ------------
        dest_script = self.prepare()

        # ----------------------------- 2) XFOIL ausführen ---------------
        exe = cfg.get("XFOIL_BIN", "xfoil.exe")
        engine = EngineFactory.create("XfoilEngine")
        engine.run_script(exe, dest_script, work)

        # ----------------------------- 3) Ergebnis referenzieren --------
        if self.cfg_key_out:
            out_name = cfg.get(self.cfg_key_out)
            if not out_name:
                log.error(f"{self.cfg_key_out} nicht in Global-Config definiert!")
                self.status = JobStatus.FAILED
                return
            produced = work / out_name
            cfg[self.cfg_key_out] = str(produced.relative_to(self.project.root))
