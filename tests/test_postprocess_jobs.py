import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.jobs import postprocess_jobs
from glacium.jobs.postprocess_jobs import (
    PostprocessSingleFensapJob,
    PostprocessMultishotJob,
)
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project
from glacium.models.job import Job


def _project(tmp_path: Path) -> Project:
    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    return Project("uid", tmp_path, cfg, paths, [])


def test_postprocess_single_fensap_dynamic_deps(tmp_path):
    project = _project(tmp_path)

    # no optional jobs present -> only FENSAP_RUN required
    assert PostprocessSingleFensapJob(project).deps == ("FENSAP_RUN",)

    class Drop(Job):
        name = "DROP3D_RUN"

        def execute(self):
            pass

    project.jobs.append(Drop(project))
    assert PostprocessSingleFensapJob(project).deps == (
        "FENSAP_RUN",
        "DROP3D_RUN",
    )

    class Ice(Job):
        name = "ICE3D_RUN"

        def execute(self):
            pass

    project.jobs.append(Ice(project))
    assert PostprocessSingleFensapJob(project).deps == (
        "FENSAP_RUN",
        "DROP3D_RUN",
        "ICE3D_RUN",
    )

def test_postprocess_single_fensap(tmp_path, monkeypatch):
    root = tmp_path
    (root / "run_FENSAP").mkdir()
    (root / "run_DROP3D").mkdir()
    project = _project(root)
    job = PostprocessSingleFensapJob(project)

    called = []

    class DummyConv:
        def __init__(self, p):
            called.append(p)
            self.root = p

        def convert(self):
            return self.root / "out.dat"

    monkeypatch.setattr(postprocess_jobs, "SingleShotConverter", DummyConv)

    written = {}

    class DummyPP:
        def __init__(self, root):
            written["root"] = root
            self.index = "IDX"

    monkeypatch.setattr(postprocess_jobs, "PostProcessor", DummyPP)

    def fake_write(index, dest):
        written["dest"] = dest
        written["index"] = index
        return Path(dest)

    monkeypatch.setattr(postprocess_jobs, "write_manifest", fake_write)

    job.execute()

    assert called == [root / "run_FENSAP", root / "run_DROP3D"]
    assert written["dest"] == root / "manifest.json"
    assert written["index"] == "IDX"
    assert written["root"] == root


def test_postprocess_multishot(tmp_path, monkeypatch):
    root = tmp_path
    ms_dir = root / "run_MULTISHOT"
    ms_dir.mkdir()
    project = _project(root)
    job = PostprocessMultishotJob(project)

    called = {}

    class DummyMSC:
        def __init__(self, p):
            called["path"] = p

        def convert_all(self):
            called["called"] = True
            return "IDX"

    monkeypatch.setattr(postprocess_jobs, "MultiShotConverter", DummyMSC)

    written = {}

    def fake_write(index, dest):
        written["index"] = index
        written["dest"] = dest
        return Path(dest)

    monkeypatch.setattr(postprocess_jobs, "write_manifest", fake_write)

    job.execute()

    assert called["path"] == ms_dir
    assert called.get("called")
    assert written["dest"] == root / "manifest.json"
    assert written["index"] == "IDX"
