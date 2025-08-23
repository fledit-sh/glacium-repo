from pathlib import Path
import sys
import types
import importlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_fensap_analysis_job(tmp_path, monkeypatch):
    pkg_path = Path(__file__).resolve().parents[1] / "glacium"
    fake_pkg = types.ModuleType("glacium")
    fake_pkg.__path__ = [str(pkg_path)]
    sys.modules.setdefault("glacium", fake_pkg)

    fake_post = types.ModuleType("glacium.post")
    fake_post.__path__ = []
    sys.modules.setdefault("glacium.post", fake_post)

    fake_analysis = types.ModuleType("glacium.post.analysis")
    sys.modules.setdefault("glacium.post.analysis", fake_analysis)
    fake_post.analysis = fake_analysis

    fake_ffp = types.ModuleType("glacium.post.analysis.fensap_flow_plots")
    fake_ffp.fensap_flow_plots = lambda *_: None
    sys.modules.setdefault("glacium.post.analysis.fensap_flow_plots", fake_ffp)

    fake_multishot = types.ModuleType("glacium.post.multishot")
    fake_multishot.run_multishot = lambda *_: None
    sys.modules.setdefault("glacium.post.multishot", fake_multishot)

    spec = importlib.util.spec_from_file_location(
        "glacium.jobs.analysis_jobs", pkg_path / "jobs" / "analysis_jobs.py"
    )
    analysis_jobs = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = analysis_jobs
    spec.loader.exec_module(analysis_jobs)
    FensapAnalysisJob = analysis_jobs.FensapAnalysisJob
    from glacium.models.config import GlobalConfig
    from glacium.managers.path_manager import PathBuilder
    from glacium.models.project import Project
    from glacium.managers.job_manager import JobManager

    run_dir = tmp_path / "run_FENSAP"
    run_dir.mkdir()
    dat = run_dir / "soln.dat"
    dat.write_text("")

    chord = 0.5
    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path, CASE_CHARACTERISTIC_LENGTH=chord)
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

    jm = JobManager(project)
    jm.run()

    out_dir = tmp_path / "analysis" / "FENSAP"
    assert called["fn"] is analysis_jobs.fensap_flow_plots
    assert called["cwd"] == tmp_path
    assert called["args"] == [dat, out_dir, "--scale", str(chord)]

