from __future__ import annotations

from pathlib import Path
from typing import Sequence

from glacium.core.base import PythonJobBase
from glacium.engines.py_engine import PyEngine
from glacium.utils.convergence import analysis, analysis_file
from glacium.utils.report_converg_fensap import build_report


class ConvergenceStatsJob(PythonJobBase):
    """Aggregate convergence statistics of a MULTISHOT run."""

    name = "CONVERGENCE_STATS"
    deps = ("MULTISHOT_RUN",)

    fn = staticmethod(analysis)

    def args(self) -> Sequence[str | Path]:
        project_root = self.project.root
        report_dir = project_root / "run_MULTISHOT"
        out_dir = project_root / "analysis" / "MULTISHOT"
        self._report_dir = report_dir
        self._out_dir = out_dir
        return [report_dir, out_dir]

    def after_run(self) -> None:
        report_dir = self._report_dir
        out_dir = self._out_dir
        if self.project.config.get("CONVERGENCE_PDF"):
            files = sorted(report_dir.glob("converg.fensap.*"))
            if files:
                PyEngine(analysis_file).run([files[-1], out_dir], cwd=self.project.root)
            build_report(out_dir)
