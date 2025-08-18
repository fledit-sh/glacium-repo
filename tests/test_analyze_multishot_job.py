import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.jobs.analysis_jobs import AnalyzeMultishotJob
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project
from glacium.managers.job_manager import JobManager
from glacium.post import analysis as post_analysis


def test_analyze_multishot_job(tmp_path, monkeypatch):
    run_dir = tmp_path / "run_MULTISHOT"
    run_dir.mkdir()
    (run_dir / "soln.fensap.000001.dat").write_text("")
    (run_dir / "swimsol.ice.000001.dat").write_text("")
    (run_dir / "ice.ice00001.stl").write_text("solid x\nendsolid x")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    paths = PathBuilder(tmp_path).build()
    paths.ensure()

    project = Project("uid", tmp_path, cfg, paths, [])
    job = AnalyzeMultishotJob(project)
    job.deps = ()
    project.jobs = [job]

    calls = {}
    cwd = {}

    def rec(name, ret=None):
        def wrapper(*args, **kwargs):
            calls[name] = args
            return ret
        return wrapper

    def fake_run_multishot(input_dir, output_dir, start_shot=None, end_shot=None):
        cwd["cwd"] = Path.cwd()
        calls["run_multishot"] = (input_dir, output_dir, start_shot, end_shot)

    monkeypatch.setattr("glacium.jobs.analysis_jobs.run_multishot", fake_run_multishot)
    monkeypatch.setattr(post_analysis, "read_wall_zone", rec("read_wall_zone", "WZ"))
    monkeypatch.setattr(post_analysis, "process_wall_zone", rec("process_wall_zone", ("PROC", "mm")))
    monkeypatch.setattr(post_analysis, "plot_ice_thickness", rec("plot_ice_thickness"))
    monkeypatch.setattr(post_analysis, "load_contours", rec("load_contours", ["SEG"]))
    monkeypatch.setattr(post_analysis, "animate_growth", rec("animate_growth"))

    jm = JobManager(project)
    jm.run()

    out_dir = tmp_path / "analysis" / "MULTISHOT"
    assert calls["run_multishot"][0] == run_dir
    assert calls["run_multishot"][1] == out_dir
    assert cwd["cwd"] == tmp_path / "run_MULTISHOT"
    assert calls["read_wall_zone"][0] == run_dir / "swimsol.ice.000001.dat"
    assert calls["process_wall_zone"][0] == "WZ"
    assert calls["plot_ice_thickness"][2] == out_dir / "swimsol.ice.000001_ice.png"
    assert calls["load_contours"][0] == "*.stl"
    assert calls["animate_growth"][1] == out_dir / "ice_growth.gif"
