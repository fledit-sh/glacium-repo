from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.jobs.analysis import MeshAnalysisJob
import importlib
analysis_jobs = importlib.import_module("glacium.jobs.analysis.mesh_analysis")
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project
from glacium.managers.job_manager import JobManager


def test_mesh_analysis_job(tmp_path, monkeypatch):
    run_dir = tmp_path / "run_MULTISHOT"
    run_dir.mkdir()
    mesh = run_dir / "lastwrap-remeshed.msh"
    mesh.write_text("")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    paths = PathBuilder(tmp_path).build()
    paths.ensure()

    project = Project("uid", tmp_path, cfg, paths, [])
    job = MeshAnalysisJob(project)
    job.deps = ()
    project.jobs = [job]

    called = {}

    class FakePyEngine:
        def __init__(self, fn):
            called["fn"] = fn

        def run(self, args, *, cwd, **_):
            called["cwd"] = cwd
            called["args"] = list(args)

    monkeypatch.setattr(analysis_jobs, "PyEngine", FakePyEngine)
    monkeypatch.setattr(analysis_jobs, "mesh_analysis", lambda *_: None)

    jm = JobManager(project)
    jm.run()

    out_dir = tmp_path / "analysis" / "MESH"
    assert called["fn"] is analysis_jobs.mesh_analysis
    assert called["cwd"] == tmp_path
    assert called["args"][0] == mesh
    assert called["args"][1] == out_dir
    assert called["args"][2] == out_dir / "mesh_report.html"

