import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.core.base import JobBase, EngineBase
from glacium.utils.JobIndex import JobFactory
from glacium.engines.engine_factory import EngineFactory
from glacium.models.config import GlobalConfig
from glacium.models.project import Project
from glacium.managers.path_manager import PathBuilder


class DummyJob(JobBase):
    name = "DUMMY_JOB"

    def execute(self) -> None:
        pass


def test_job_factory_register(monkeypatch, tmp_path):
    monkeypatch.setattr(JobFactory, "_jobs", {})
    monkeypatch.setattr(JobFactory, "_loaded", True)

    JobFactory.register(DummyJob)

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    paths = PathBuilder(tmp_path).build()
    project = Project("uid", tmp_path, cfg, paths, [])

    job = JobFactory.create("DUMMY_JOB", project)
    assert isinstance(job, DummyJob)
    assert "DUMMY_JOB" in JobFactory.list()


class DummyEngine(EngineBase):
    def run_script(self, script: Path, work: Path) -> None:
        pass


def test_engine_factory_register(monkeypatch):
    monkeypatch.setattr(EngineFactory, "_engines", {})

    EngineFactory.register(DummyEngine)

    engine = EngineFactory.create("DummyEngine")
    assert isinstance(engine, DummyEngine)
    assert "DummyEngine" in EngineFactory.list()
