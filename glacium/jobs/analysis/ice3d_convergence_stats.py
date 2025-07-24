from __future__ import annotations

from glacium.models.job import Job
from glacium.engines.py_engine import PyEngine
from glacium.utils.convergence import analysis_file
from glacium.utils.report_converg_fensap import build_report


class Ice3dConvergenceStatsJob(Job):
    """Generate convergence plots for an ICE3D run."""

    name = "ICE3D_CONVERGENCE_STATS"
    deps = ("ICE3D_RUN",)

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        converg_file = project_root / "run_ICE3D" / "iceconv.dat"
        out_dir = project_root / "analysis" / "ICE3D"

        engine = PyEngine(analysis_file)
        engine.run([converg_file, out_dir], cwd=project_root)

        if self.project.config.get("CONVERGENCE_PDF"):
            build_report(out_dir)
