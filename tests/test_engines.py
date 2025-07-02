import time
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
import pytest

from glacium.engines.base_engine import BaseEngine, XfoilEngine, DummyEngine
from glacium.engines.xfoil_base import XfoilScriptJob
from glacium.engines.pointwise import PointwiseEngine, PointwiseScriptJob
from glacium.engines.fensap import FensapEngine
from glacium.jobs.fensap_jobs import (
    FensapRunJob,
    Drop3dRunJob,
    Ice3dRunJob,
    MultiShotRunJob,
)
from glacium.engines.fluent2fensap import Fluent2FensapJob
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


def test_pointwise_script_job_runs_in_project_root(monkeypatch, tmp_path):
    """Ensure ``PointwiseScriptJob`` executes from project root."""
    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "test.glf.j2").write_text("puts hello")

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

    called = {}

    def fake_run(self, cmd, *, cwd, stdin=None):
        called["cmd"] = cmd
        called["cwd"] = cwd
        called["stdin"] = stdin

    monkeypatch.setattr(BaseEngine, "run", fake_run)

    job.execute()

    assert called["cmd"] == ["cat"]
    assert called["cwd"] == project.root


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
    (template_root / "FENSAP.FENSAP.solvercmd.j2").write_text("exit 0")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = "sh"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = FensapRunJob(project)
    job.execute()
    assert (paths.solver_dir("run_FENSAP") / ".solvercmd").exists()


def test_fensap_run_job_calls_base_engine(monkeypatch, tmp_path):
    """Ensure ``BaseEngine.run`` is executed with configured executable."""
    _SharedState._SharedState__shared_state.clear()

    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "FENSAP.FENSAP.files.j2").write_text("files")
    (template_root / "FENSAP.FENSAP.par.j2").write_text("par")
    (template_root / "FENSAP.FENSAP.solvercmd.j2").write_text("exit 0")

    exe = tmp_path / "bin" / "nti_sh.exe"
    exe.parent.mkdir()
    exe.write_text("")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = str(exe)

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = FensapRunJob(project)

    called = {}

    def fake_run(self, cmd, *, cwd, stdin=None):
        called["cmd"] = cmd
        called["cwd"] = cwd
        called["stdin"] = stdin

    monkeypatch.setattr(BaseEngine, "run", fake_run)

    job.execute()

    work = paths.solver_dir("run_FENSAP")
    solvercmd = work / ".solvercmd"

    assert solvercmd.exists()
    assert called["cmd"] == [str(exe), str(solvercmd)]
    assert called["cwd"] == work


def test_multishot_run_job(tmp_path):
    _SharedState._SharedState__shared_state.clear()
    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "MULTISHOT.meshingSizes.scm.j2").write_text("scm")
    (template_root / "MULTISHOT.custom_remeshing.sh.j2").write_text("custom")
    (template_root / "MULTISHOT.solvercmd.j2").write_text("exit 0")
    (template_root / "MULTISHOT.files.j2").write_text("files")
    (template_root / "MULTISHOT.config.par.j2").write_text("cfg")
    (template_root / "MULTISHOT.fensap.par.j2").write_text("fsp")
    (template_root / "MULTISHOT.drop.par.j2").write_text("drop")
    (template_root / "MULTISHOT.ice.par.j2").write_text("ice")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = "sh"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = MultiShotRunJob(project)
    job.execute()
    assert (paths.solver_dir("run_MULTISHOT") / ".solvercmd").exists()


def test_multishot_run_job_calls_base_engine(monkeypatch, tmp_path):
    """Ensure ``BaseEngine.run`` is executed with configured executable."""
    _SharedState._SharedState__shared_state.clear()

    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "MULTISHOT.meshingSizes.scm.j2").write_text("scm")
    (template_root / "MULTISHOT.custom_remeshing.sh.j2").write_text("custom")
    (template_root / "MULTISHOT.solvercmd.j2").write_text("exit 0")
    (template_root / "MULTISHOT.files.j2").write_text("files")
    (template_root / "MULTISHOT.config.par.j2").write_text("cfg")
    (template_root / "MULTISHOT.fensap.par.j2").write_text("fsp")
    (template_root / "MULTISHOT.drop.par.j2").write_text("drop")
    (template_root / "MULTISHOT.ice.par.j2").write_text("ice")

    exe = tmp_path / "bin" / "nti_sh.exe"
    exe.parent.mkdir()
    exe.write_text("")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = str(exe)

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = MultiShotRunJob(project)

    called = {}

    def fake_run(self, cmd, *, cwd, stdin=None):
        called["cmd"] = cmd
        called["cwd"] = cwd
        called["stdin"] = stdin

    monkeypatch.setattr(BaseEngine, "run", fake_run)

    job.execute()

    work = paths.solver_dir("run_MULTISHOT")
    solvercmd = work / ".solvercmd"

    assert solvercmd.exists()
    assert called["cmd"] == [str(exe), str(solvercmd)]
    assert called["cwd"] == work


def test_drop3d_run_job(tmp_path):
    _SharedState._SharedState__shared_state.clear()
    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "FENSAP.DROP3D.files.j2").write_text("files")
    (template_root / "FENSAP.DROP3D.par.j2").write_text("par")
    (template_root / "FENSAP.DROP3D.solvercmd.j2").write_text("exit 0")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = "sh"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = Drop3dRunJob(project)
    job.execute()
    assert (paths.solver_dir("run_DROP3D") / ".solvercmd").exists()


def test_drop3d_run_job_calls_base_engine(monkeypatch, tmp_path):
    """Ensure ``BaseEngine.run`` is executed with configured executable."""
    _SharedState._SharedState__shared_state.clear()

    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "FENSAP.DROP3D.files.j2").write_text("files")
    (template_root / "FENSAP.DROP3D.par.j2").write_text("par")
    (template_root / "FENSAP.DROP3D.solvercmd.j2").write_text("exit 0")

    exe = tmp_path / "bin" / "nti_sh.exe"
    exe.parent.mkdir()
    exe.write_text("")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = str(exe)

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = Drop3dRunJob(project)

    called = {}

    def fake_run(self, cmd, *, cwd, stdin=None):
        called["cmd"] = cmd
        called["cwd"] = cwd
        called["stdin"] = stdin

    monkeypatch.setattr(BaseEngine, "run", fake_run)

    job.execute()

    work = paths.solver_dir("run_DROP3D")
    solvercmd = work / ".solvercmd"

    assert solvercmd.exists()
    assert called["cmd"] == [str(exe), str(solvercmd)]
    assert called["cwd"] == work


def test_ice3d_run_job(tmp_path):
    _SharedState._SharedState__shared_state.clear()
    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "FENSAP.ICE3D.custom_remeshing.sh.j2").write_text("custom")
    (template_root / "FENSAP.ICE3D.remeshing.jou.j2").write_text("jou")
    (template_root / "FENSAP.ICE3D.meshingSizes.scm.j2").write_text("scm")
    (template_root / "FENSAP.ICE3D.files.j2").write_text("files")
    (template_root / "FENSAP.ICE3D.par.j2").write_text("par")
    (template_root / "FENSAP.ICE3D.solvercmd.j2").write_text("exit 0")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = "sh"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = Ice3dRunJob(project)
    job.execute()
    assert (paths.solver_dir("run_ICE3D") / ".solvercmd").exists()


def test_ice3d_run_job_calls_base_engine(monkeypatch, tmp_path):
    """Ensure ``BaseEngine.run`` is executed with configured executable."""
    _SharedState._SharedState__shared_state.clear()

    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "FENSAP.ICE3D.custom_remeshing.sh.j2").write_text("custom")
    (template_root / "FENSAP.ICE3D.remeshing.jou.j2").write_text("jou")
    (template_root / "FENSAP.ICE3D.meshingSizes.scm.j2").write_text("scm")
    (template_root / "FENSAP.ICE3D.files.j2").write_text("files")
    (template_root / "FENSAP.ICE3D.par.j2").write_text("par")
    (template_root / "FENSAP.ICE3D.solvercmd.j2").write_text("exit 0")

    exe = tmp_path / "bin" / "nti_sh.exe"
    exe.parent.mkdir()
    exe.write_text("")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = str(exe)

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = Ice3dRunJob(project)

    called = {}

    def fake_run(self, cmd, *, cwd, stdin=None):
        called["cmd"] = cmd
        called["cwd"] = cwd
        called["stdin"] = stdin

    monkeypatch.setattr(BaseEngine, "run", fake_run)

    job.execute()

    work = paths.solver_dir("run_ICE3D")
    solvercmd = work / ".solvercmd"

    assert solvercmd.exists()
    assert called["cmd"] == [str(exe), str(solvercmd)]
    assert called["cwd"] == work


def test_fluent2fensap_job(monkeypatch, tmp_path):
    _SharedState._SharedState__shared_state.clear()

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    exe = tmp_path / "bin" / "fluent2fensap.exe"
    exe.parent.mkdir()
    exe.write_text("")
    cfg["FLUENT2FENSAP_EXE"] = str(exe)
    cfg["PWS_GRID_PATH"] = "mesh.cas"
    cfg["ICE_GRID_FILE"] = "old.grid"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()

    work = paths.solver_dir("mesh")
    (work / "mesh.cas").write_text("case")

    project = Project("uid", tmp_path, cfg, paths, [])
    job = Fluent2FensapJob(project)

    def fake_run(self, cmd, *, cwd, stdin=None):
        (work / "mesh.grid").write_text("grid")
        run_call["cmd"] = cmd
        run_call["cwd"] = cwd

    run_call = {}
    monkeypatch.setattr(BaseEngine, "run", fake_run)

    job.execute()

    dest = paths.mesh_dir() / "mesh.grid"
    assert dest.exists()
    assert run_call["cmd"] == [str(exe), "mesh.cas", "mesh"]
    assert run_call["cwd"] == work
    rel = dest.relative_to(project.root)
    assert cfg["FSP_FILES_GRID"] == str(rel)
    assert cfg["ICE_GRID_FILE"] == str(rel)

