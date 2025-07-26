from __future__ import annotations

from pathlib import Path
from typing import Sequence

from glacium.core.base import PythonJobBase
from glacium.analysis import ConvergenceAnalyzer
from glacium.utils.report_converg_fensap import build_report

_analyzer = ConvergenceAnalyzer()


class Ice3dConvergenceStatsJob(PythonJobBase):
    """Generate convergence plots for an ICE3D run."""

    name = "ICE3D_CONVERGENCE_STATS"
    deps = ("ICE3D_RUN",)

    fn = staticmethod(_analyzer.analysis_file)

    def args(self) -> Sequence[str | Path]:
        project_root = self.project.root
        converg_file = project_root / "run_ICE3D" / "iceconv.dat"
        out_dir = project_root / "analysis" / "ICE3D"
        self._out_dir = out_dir
        return [converg_file, out_dir]

    def after_run(self) -> None:
        if self.project.config.get("CONVERGENCE_PDF"):
            build_report(self._out_dir)
