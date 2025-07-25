from __future__ import annotations

from pathlib import Path
from typing import Sequence

from glacium.core.base import PythonJobBase
from glacium.engines.py_engine import PyEngine
from glacium.utils.mesh_analysis import mesh_analysis


class MeshAnalysisJob(PythonJobBase):
    """Generate mesh screenshots and HTML report."""

    name = "MESH_ANALYSIS"
    deps: tuple[str, ...] = ()

    def args(self) -> Sequence[str | Path]:
        project_root = self.project.root
        meshfile = project_root / "run_MULTISHOT" / "lastwrap-remeshed.msh"
        out_dir = project_root / "analysis" / "MESH"
        return [meshfile, out_dir, out_dir / "mesh_report.html"]

    def execute(self) -> None:  # noqa: D401
        engine = PyEngine(mesh_analysis)
        engine.run(self.args(), cwd=self.project.root)
