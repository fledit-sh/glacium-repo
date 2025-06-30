import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.engines.fluent2fensap import Fluent2FensapJob
from glacium.engines.base_engine import BaseEngine
from glacium.models.config import GlobalConfig
from glacium.managers.PathManager import PathBuilder, _SharedState
from glacium.models.project import Project


def test_fluent2fensap_default(monkeypatch, tmp_path):
    _SharedState._SharedState__shared_state.clear()

    exe = tmp_path / "bin" / "fluent2fensap.exe"
    exe.parent.mkdir()
    exe.write_text("")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FLUENT2FENSAP_EXE"] = str(exe)
    cfg["PWS_GRID_PATH"] = "GCI.cas"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()

    work = paths.solver_dir("mesh")
    (work / "GCI.cas").write_text("case")

    project = Project("uid", tmp_path, cfg, paths, [])
    job = Fluent2FensapJob(project)

    called = {}

    def fake_run(self, cmd, *, cwd, stdin=None):
        (work / "GCI.grid").write_text("grid")
        called["cmd"] = cmd
        called["cwd"] = cwd

    monkeypatch.setattr(BaseEngine, "run", fake_run)

    job.execute()

    dest = paths.mesh_dir() / "GCI.grid"
    assert dest.exists()
    assert called["cmd"] == [str(exe), "GCI.cas", "GCI"]
    assert called["cwd"] == work
    rel = dest.relative_to(project.root)
    expected = str(Path("..") / rel)
    assert cfg["FSP_FILES_GRID"] == expected
