from __future__ import annotations

from pathlib import Path
from typing import Sequence

from glacium.core.base import PythonJobBase
from glacium.engines.py_engine import PyEngine
from glacium.utils.postprocess_fensap import fensap_analysis


class FensapAnalysisJob(PythonJobBase):
    """Generate slice plots from FENSAP results."""

    name = "FENSAP_ANALYSIS"
    deps = ("POSTPROCESS_SINGLE_FENSAP",)

    def args(self) -> Sequence[str | Path]:
        project_root = self.project.root
        dat_file = project_root / "run_FENSAP" / "soln.fensap.dat"
        out_dir = project_root / "analysis" / "FENSAP"
        return [dat_file, out_dir]

    def execute(self) -> None:  # noqa: D401
        engine = PyEngine(fensap_analysis)
        engine.run(self.args(), cwd=self.project.root)
