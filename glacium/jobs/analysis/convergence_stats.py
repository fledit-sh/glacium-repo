from __future__ import annotations

from glacium.models.job import Job
from glacium.engines.py_engine import PyEngine
from glacium.utils.convergence import analysis, analysis_file
from glacium.utils.report_converg_fensap import build_report


class ConvergenceStatsJob(Job):
    """Aggregate convergence statistics of a MULTISHOT run."""

    name = "CONVERGENCE_STATS"
    deps = ("MULTISHOT_RUN",)

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        report_dir = project_root / "run_MULTISHOT"
        out_dir = project_root / "analysis" / "MULTISHOT"

        engine = PyEngine(analysis)
        engine.run([report_dir, out_dir], cwd=project_root)

        if self.project.config.get("CONVERGENCE_PDF"):
            files = sorted(report_dir.glob("converg.fensap.*"))
            if files:
                PyEngine(analysis_file).run([files[-1], out_dir], cwd=project_root)
            build_report(out_dir)
