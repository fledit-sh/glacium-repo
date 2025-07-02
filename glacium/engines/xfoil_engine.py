"""XFOIL Engine – Refine Job

Rendert ein Batch‑Skript aus Jinja‑Template und führt XFOIL headless aus.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from glacium.managers.TemplateManager import TemplateManager
from glacium.models.job import Job
from glacium.utils.logging import log


class XfoilRefineJob(Job):
    """Verfeinert das Eingangsprofil durch Punktverdichtung."""

    name = "XFOIL_REFINE"
    deps = ()

    _TEMPLATE = Path("XFOIL.increasepoints.in.j2")

    def execute(self):  # noqa: D401
        cfg = self.project.config
        paths = self.project.paths
        work = paths.solver_dir("xfoil")  # → runs/<uid>/xfoil

        # ------------------------------------------------------------------
        # 1) Skript rendern (Ziel = gleiche Datei OHNE .j2)
        # ------------------------------------------------------------------
        dest_script = work / self._TEMPLATE.with_suffix("")
        TemplateManager().render_to_file(self._TEMPLATE, cfg.extras, dest_script)

        # ------------------------------------------------------------------
        # 2) XFOIL Binary bestimmen
        # ------------------------------------------------------------------
        exe = cfg.get("XFOIL_BIN", "xfoil.exe")

        # ------------------------------------------------------------------
        # 3) Headless ausführen
        # ------------------------------------------------------------------
        log.info(f"🚀  {exe} < {dest_script.name}")
        with dest_script.open("r") as stdin:
            subprocess.check_call([exe], stdin=stdin, cwd=work)

        # ------------------------------------------------------------------
        # 4) Ergebnis in Config ablegen (für nachfolgende Jobs)
        # ------------------------------------------------------------------
        out_file = work / "refined.dat"
        cfg["PWS_PROFILE1"] = str(out_file.relative_to(self.project.root))
