import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from glacium.managers.project_manager import ProjectManager, RecipeManager


class DummyJob:
    name = "DUMMY"

    def __init__(self, project):
        self.project = project

    def prepare(self):
        pass


class DummyRecipe:
    def __init__(self, jobs):
        self._jobs = jobs

    def build(self, project):
        return [job(project) for job in self._jobs]


def test_create_and_load(tmp_path, monkeypatch):
    pm = ProjectManager(tmp_path)
    monkeypatch.setattr(ProjectManager, "_uid", staticmethod(lambda name: "UID"))
    monkeypatch.setattr(ProjectManager, "_render_templates", lambda *a, **k: None)
    monkeypatch.setattr(ProjectManager, "_load_jobs", lambda self, project, **k: None)

    airfoil = tmp_path / "foil.dat"
    airfoil.write_text("data")

    project = pm.create("proj", "recipe", airfoil)

    assert project.uid == "UID"
    assert (tmp_path / "UID" / "_cfg" / "global_config.yaml").exists()
    assert (tmp_path / "UID" / "_data" / "foil.dat").exists()

    pm._cache.clear()
    loaded = pm.load("UID")
    assert loaded.uid == project.uid
    assert loaded.paths.root == project.paths.root


def test_refresh_jobs(tmp_path, monkeypatch):
    pm = ProjectManager(tmp_path)
    monkeypatch.setattr(ProjectManager, "_uid", staticmethod(lambda n: "RJOB"))
    monkeypatch.setattr(ProjectManager, "_render_templates", lambda *a, **k: None)

    class FakeJobManager:
        def __init__(self, proj, jobs=None):
            if jobs is None:
                jobs = proj.jobs
            self._jobs = {j.name: j for j in jobs}
        def _save_status(self):
            self.saved = True

    # initialise project with one job manager instance
    def fake_load_jobs(self, project, **k):
        job = DummyJob(project)
        project.jobs.append(job)
        project.job_manager = FakeJobManager(project, [job])

    monkeypatch.setattr(ProjectManager, "_load_jobs", fake_load_jobs)

    airfoil = tmp_path / "foil.dat"
    airfoil.write_text("data")
    project = pm.create("proj", "recipe", airfoil)

    monkeypatch.setattr("glacium.managers.project_manager.JobManager", FakeJobManager)
    monkeypatch.setattr(RecipeManager, "create", lambda name: DummyRecipe([DummyJob, DummyJob]))

    pm.refresh_jobs(project.uid)

    assert isinstance(project.job_manager, FakeJobManager)
    assert len(project.jobs) == 1
