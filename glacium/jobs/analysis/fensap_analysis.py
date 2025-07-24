from __future__ import annotations

from glacium.models.job import Job
from glacium.engines.py_engine import PyEngine
from glacium.utils.postprocess_fensap import fensap_analysis


class FensapAnalysisJob(Job):
    """Generate slice plots from FENSAP results."""

    name = "FENSAP_ANALYSIS"
    deps = ("POSTPROCESS_SINGLE_FENSAP",)

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        dat_file = project_root / "run_FENSAP" / "soln.fensap.dat"
        out_dir = project_root / "analysis" / "FENSAP"

        engine = PyEngine(fensap_analysis)
        engine.run([dat_file, out_dir], cwd=project_root)
