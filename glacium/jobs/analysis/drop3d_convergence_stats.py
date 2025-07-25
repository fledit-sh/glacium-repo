from __future__ import annotations

from pathlib import Path
from typing import Sequence

from glacium.core.base import PythonJobBase
from glacium.utils.convergence import analysis_file
from glacium.utils.report_converg_fensap import build_report


class Drop3dConvergenceStatsJob(PythonJobBase):
    """Generate convergence plots for a DROP3D run."""

    name = "DROP3D_CONVERGENCE_STATS"
    deps = ("DROP3D_RUN",)

    fn = staticmethod(analysis_file)

    def args(self) -> Sequence[str | Path]:
        project_root = self.project.root
        converg_file = project_root / "run_DROP3D" / "converg"
        out_dir = project_root / "analysis" / "DROP3D"
        self._out_dir = out_dir
        return [converg_file, out_dir]

    def after_run(self) -> None:
        if self.project.config.get("CONVERGENCE_PDF"):
            build_report(self._out_dir)
