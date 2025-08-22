from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.jobs.analysis_jobs import FensapAnalysisJob
import glacium.jobs.analysis_jobs as analysis_jobs
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project
from glacium.managers.job_manager import JobManager


def test_fensap_analysis_job(tmp_path, monkeypatch):
    run_dir = tmp_path / "run_FENSAP"
    run_dir.mkdir()
    dat = run_dir / "soln.dat"
    dat.write_text("")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    paths = PathBuilder(tmp_path).build()
    paths.ensure()

    project = Project("uid", tmp_path, cfg, paths, [])
    job = FensapAnalysisJob(project)
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
    monkeypatch.setattr(analysis_jobs, "fensap_flow_plots", lambda *_: None)

    jm = JobManager(project)
    jm.run()

    out_dir = tmp_path / "analysis" / "FENSAP"
    assert called["fn"] is analysis_jobs.fensap_flow_plots
    assert called["cwd"] == tmp_path
    assert called["args"] == [dat, out_dir]
