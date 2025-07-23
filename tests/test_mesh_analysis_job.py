from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.jobs.analysis_jobs import MeshAnalysisJob
import glacium.jobs.analysis_jobs as analysis_jobs
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

    def fake_mesh_analysis(cwd, args):
        called["cwd"] = cwd
        called["args"] = list(args)

    monkeypatch.setattr(analysis_jobs, "mesh_analysis", fake_mesh_analysis)

    jm = JobManager(project)
    jm.run()

    out_dir = tmp_path / "analysis" / "MESH"
    assert called["cwd"] == tmp_path
    assert called["args"][0] == mesh
    assert called["args"][1] == out_dir
    assert called["args"][2] == out_dir / "mesh_report.html"

