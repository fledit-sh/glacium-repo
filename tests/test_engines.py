import time
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
import pytest

from glacium.engines.base_engine import BaseEngine, XfoilEngine, DummyEngine
from glacium.engines.XfoilBase import XfoilScriptJob
from glacium.engines.pointwise import PointwiseEngine, PointwiseScriptJob
from glacium.engines.fensap import FensapEngine, FensapRunJob
from glacium.models.config import GlobalConfig
from glacium.managers.PathManager import PathBuilder, _SharedState
from glacium.managers.TemplateManager import TemplateManager
from glacium.models.project import Project


def test_base_engine_run(tmp_path):
    f = tmp_path / "inp"
    f.write_text("data")
    engine = BaseEngine()
    with f.open("r") as stdin:
        engine.run(["cat"], cwd=tmp_path, stdin=stdin)


def test_xfoil_engine_run_script(tmp_path):
    script = tmp_path / "script.in"
    script.write_text("hi")
    engine = XfoilEngine()
    engine.run_script("cat", script, tmp_path)


def test_dummy_engine_timer(monkeypatch):
    engine = DummyEngine()
    called = []
    monkeypatch.setattr(time, "sleep", lambda s: called.append(s))
    engine.run_job("demo")
    assert called == [30]


def test_xfoil_script_job(tmp_path):
    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    template = template_root / "test.in.j2"
    template.write_text("HELLO")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["XFOIL_BIN"] = "cat"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    class TestJob(XfoilScriptJob):
        name = "TEST"
        template = Path("test.in.j2")
        cfg_key_out = None

    project = Project("uid", tmp_path, cfg, paths, [])
    job = TestJob(project)
    job.execute()
    assert (paths.solver_dir("xfoil") / "test.in").exists()


def test_pointwise_engine_run_script(tmp_path):
    script = tmp_path / "script.glf"
    script.write_text("puts hi")
    engine = PointwiseEngine()
    engine.run_script("cat", script, tmp_path)


def test_pointwise_script_job(tmp_path):
    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    template = template_root / "test.glf.j2"
    template.write_text("puts hello")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["POINTWISE_BIN"] = "cat"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    class TestJob(PointwiseScriptJob):
        name = "TESTPW"
        template = Path("test.glf.j2")
        cfg_key_out = None

    project = Project("uid", tmp_path, cfg, paths, [])
    job = TestJob(project)
    job.execute()
    assert (paths.solver_dir("pointwise") / "test.glf").exists()


def test_fensap_engine_run_script(tmp_path):
    _SharedState._SharedState__shared_state.clear()
    script = tmp_path / "run.sh"
    script.write_text("exit 0")
    engine = FensapEngine()
    engine.run_script("sh", script, tmp_path)


def test_fensap_run_job(tmp_path):
    _SharedState._SharedState__shared_state.clear()
    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "FENSAP.FENSAP.files.j2").write_text("files")
    (template_root / "FENSAP.FENSAP.par.j2").write_text("par")
    (template_root / "FENSAP.solvercmd.j2").write_text("exit 0")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = "sh"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = FensapRunJob(project)
    job.execute()
    assert (paths.solver_dir("run_FENSAP") / ".solvercmd").exists()

