from __future__ import annotations

from glacium.models.job import Job
from glacium.engines.py_engine import PyEngine
from glacium.utils.mesh_analysis import mesh_analysis


class MeshAnalysisJob(Job):
    """Generate mesh screenshots and HTML report."""

    name = "MESH_ANALYSIS"
    deps: tuple[str, ...] = ()

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        meshfile = project_root / "run_MULTISHOT" / "lastwrap-remeshed.msh"
        out_dir = project_root / "analysis" / "MESH"

        engine = PyEngine(mesh_analysis)
        engine.run([meshfile, out_dir, out_dir / "mesh_report.html"], cwd=project_root)
