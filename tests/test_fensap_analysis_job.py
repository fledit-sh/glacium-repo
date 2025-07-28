from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.jobs.analysis_jobs import FensapAnalysisJob
import glacium.jobs.analysis_jobs as analysis_jobs
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project
from glacium.managers.job_manager import JobManager
from glacium.post import analysis as post_analysis
import pandas as pd


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
    monkeypatch.setattr(analysis_jobs, "fensap_analysis", lambda *_: None)

    def rec(name, ret=None):
        def wrapper(*args, **kwargs):
            called[name] = args
            return ret
        return wrapper

    cp_df = pd.DataFrame({"x_c": [0.0], "Cp": [0.0]})

    monkeypatch.setattr(post_analysis, "read_tec_ascii", rec("read_tec_ascii", "DF"))
    monkeypatch.setattr(post_analysis, "compute_cp", rec("compute_cp", cp_df))

    def fake_plot_cp_directional(*args):
        called["plot_cp_directional"] = args
        Path(args[5]).write_text("img")

    monkeypatch.setattr(post_analysis, "plot_cp_directional", fake_plot_cp_directional)

    jm = JobManager(project)
    jm.run()

    out_dir = tmp_path / "analysis" / "FENSAP"
    assert called["fn"] is analysis_jobs.fensap_analysis
    assert called["cwd"] == tmp_path
    assert called["args"] == [dat, out_dir]
    assert (out_dir / "soln.fensap_cp.png").exists()
    assert (out_dir / "cp_curve.csv").exists()
    res_file = tmp_path / "results.yaml"
    assert res_file.exists()
    assert res_file.read_text().strip() == "MOMENTUM_COEFFICIENT: 0.0" 
