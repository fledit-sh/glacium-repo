from pathlib import Path

import yaml
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.api import Run
from glacium.managers.template_manager import TemplateManager
from glacium.managers.job_manager import JobManager


def test_project_api_run(tmp_path, monkeypatch):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Run(tmp_path)
    project = run.create()

    called = {}

    def fake_run(self, jobs=None):
        called["jobs"] = jobs

    monkeypatch.setattr(JobManager, "run", fake_run)

    project.run()
    assert called["jobs"] is None

    project.run("XFOIL_REFINE")
    assert called["jobs"] == ["XFOIL_REFINE"]


def test_run_load(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Run(tmp_path)
    project = run.create()

    loaded = run.load(project.uid)
    assert loaded.uid == project.uid


def test_project_add_job(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Run(tmp_path)
    project = run.create()

    added = project.add_job("CONVERGENCE_STATS")
    assert "CONVERGENCE_STATS" in added
    assert "MULTISHOT_RUN" in added

    jobs_yaml = tmp_path / project.uid / "_cfg" / "jobs.yaml"
    data = yaml.safe_load(jobs_yaml.read_text())
    assert "CONVERGENCE_STATS" in data
    assert "MULTISHOT_RUN" in data

    cfg_file = tmp_path / project.uid / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    assert cfg["RECIPE"] == "CUSTOM"


def test_load_add_job_and_run(tmp_path, monkeypatch):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Run(tmp_path)
    project = run.create()

    uid = project.uid

    proj = Run(tmp_path).load(uid)
    assert proj.uid == uid

    proj.add_job("POINTWISE_MESH2")

    jobs_yaml = tmp_path / uid / "_cfg" / "jobs.yaml"
    data = yaml.safe_load(jobs_yaml.read_text())
    assert "POINTWISE_MESH2" in data
    assert "POINTWISE_GCI" in data

    called = {}

    def fake_run(self, jobs=None):
        called["jobs"] = jobs

    monkeypatch.setattr(JobManager, "run", fake_run)

    proj.run("POINTWISE_MESH2")
    assert called["jobs"] == ["POINTWISE_MESH2"]
