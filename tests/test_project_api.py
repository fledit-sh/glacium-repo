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
