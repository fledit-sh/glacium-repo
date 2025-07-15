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
from glacium.engines.fensap import FensapEngine, FensapScriptJob
from glacium.engines.engine_factory import EngineFactory
from glacium.jobs.fensap_jobs import (
    FensapRunJob,
    Drop3dRunJob,
    Ice3dRunJob,
    MultiShotRunJob,
)
import glacium.jobs.fensap_jobs as fensap_jobs
from glacium.engines.fluent2fensap import Fluent2FensapJob
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.managers.template_manager import TemplateManager
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


def test_pointwise_engine_run_script(monkeypatch, tmp_path):
    """Ensure ``PointwiseEngine.run_script`` passes script as argument."""

    script = tmp_path / "script.glf"
    script.write_text("puts hi")
    engine = PointwiseEngine()

    called = {}

    def fake_run(self, cmd, *, cwd, stdin=None):
        called["cmd"] = cmd
        called["cwd"] = cwd
        called["stdin"] = stdin

    monkeypatch.setattr(BaseEngine, "run", fake_run)

    engine.run_script("cat", script, tmp_path)

    assert called["cmd"] == ["cat", str(script)]
    assert called["cwd"] == tmp_path
    assert called["stdin"] is None


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

    expected_script = project.paths.solver_dir("pointwise") / "test.glf"

    assert called["cmd"] == ["cat", str(expected_script)]
    assert called["cwd"] == project.paths.solver_dir("pointwise")
    assert called["stdin"] is None


def test_fensap_engine_run_script(tmp_path):
    script = tmp_path / "run.sh"
    script.write_text("exit 0")
    engine = FensapEngine()
    engine.run_script("sh", script, tmp_path)


def test_fensap_run_job(tmp_path):
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


def test_multishot_run_job(monkeypatch, tmp_path):
    template_root = tmp_path / "templates"
    template_root.mkdir()
    monkeypatch.setattr(fensap_jobs, "__file__", str(tmp_path / "pkg" / "fensap_jobs.py"))
    (template_root / "MULTISHOT.meshingSizes.scm.j2").write_text("scm")
    (template_root / "MULTISHOT.custom_remeshing.sh.j2").write_text("custom")
    (template_root / "MULTISHOT.solvercmd.j2").write_text("exit 0")
    (template_root / "MULTISHOT.files.j2").write_text("files")
    (template_root / "MULTISHOT.config.par.j2").write_text("cfg")
    (template_root / "MULTISHOT.fensap.par.j2").write_text("fsp")
    (template_root / "MULTISHOT.drop.par.j2").write_text("drop")
    (template_root / "MULTISHOT.ice.par.j2").write_text("ice")
    (template_root / "MULTISHOT.create-2.5D-mesh.bin.j2").write_text("bin")
    (template_root / "MULTISHOT.remeshing.jou.j2").write_text("jou")
    (template_root / "MULTISHOT.fluent_config.jou.j2").write_text("fluent")

    (template_root / "config.fensap.j2").write_text("fensap")
    (template_root / "config.drop.j2").write_text("drop")
    (template_root / "config.ice.j2").write_text("ice")
    (template_root / "files.drop.j2").write_text("fdrop")
    (template_root / "files.fensap.j2").write_text("ffsp")


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

    template_root = tmp_path / "templates"
    template_root.mkdir()
    monkeypatch.setattr(fensap_jobs, "__file__", str(tmp_path / "pkg" / "fensap_jobs.py"))
    (template_root / "MULTISHOT.meshingSizes.scm.j2").write_text("scm")
    (template_root / "MULTISHOT.custom_remeshing.sh.j2").write_text("custom")
    (template_root / "MULTISHOT.solvercmd.j2").write_text("exit 0")
    (template_root / "MULTISHOT.files.j2").write_text("files")
    (template_root / "MULTISHOT.config.par.j2").write_text("cfg")
    (template_root / "MULTISHOT.fensap.par.j2").write_text("fsp")
    (template_root / "MULTISHOT.drop.par.j2").write_text("drop")
    (template_root / "MULTISHOT.ice.par.j2").write_text("ice")
    (template_root / "MULTISHOT.create-2.5D-mesh.bin.j2").write_text("bin")
    (template_root / "MULTISHOT.remeshing.jou.j2").write_text("jou")
    (template_root / "MULTISHOT.fluent_config.jou.j2").write_text("fluent")
    (template_root / "config.fensap.j2").write_text("fensap")
    (template_root / "config.drop.j2").write_text("drop")
    (template_root / "config.ice.j2").write_text("ice")
    (template_root / "files.drop.j2").write_text("fdrop")
    (template_root / "files.fensap.j2").write_text("ffsp")

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


@pytest.mark.parametrize("count", [3, 5])
def test_multishot_run_job_renders_batch(monkeypatch, tmp_path, count):
    template_root = tmp_path / "templates"
    template_root.mkdir()
    monkeypatch.setattr(fensap_jobs, "__file__", str(tmp_path / "pkg" / "fensap_jobs.py"))
    # required templates
    (template_root / "MULTISHOT.meshingSizes.scm.j2").write_text("scm")
    (template_root / "MULTISHOT.custom_remeshing.sh.j2").write_text("custom")
    (template_root / "MULTISHOT.solvercmd.j2").write_text("exit 0")
    (template_root / "MULTISHOT.files.j2").write_text("files")
    (template_root / "MULTISHOT.config.par.j2").write_text("cfg")
    (template_root / "MULTISHOT.fensap.par.j2").write_text("fsp")
    (template_root / "MULTISHOT.drop.par.j2").write_text("drop")
    (template_root / "MULTISHOT.ice.par.j2").write_text("ice")
    (template_root / "MULTISHOT.create-2.5D-mesh.bin.j2").write_text("bin")
    (template_root / "MULTISHOT.remeshing.jou.j2").write_text("jou")
    (template_root / "MULTISHOT.fluent_config.jou.j2").write_text("fluent")

    # shot templates
    (template_root / "config.fensap.j2").write_text("fensap")
    (template_root / "config.drop.j2").write_text("drop")
    (template_root / "config.ice.j2").write_text("ice")
    (template_root / "files.drop.j2").write_text("fdrop")
    (template_root / "files.fensap.j2").write_text("ffsp")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = "sh"
    cfg["MULTISHOT_COUNT"] = count

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = MultiShotRunJob(project)
    job.execute()
    work = paths.solver_dir("run_MULTISHOT")
    assert len(list(work.glob("config.fensap.*"))) == count
    assert len(list(work.glob("config.drop.*"))) == count
    for i in range(1, count + 1):
        idx = f"{i:06d}"
        assert (work / f"config.fensap.{idx}").exists()
        assert (work / f"config.drop.{idx}").exists()


def test_multishot_initial_type(monkeypatch, tmp_path):
    template_root = tmp_path / "templates"
    template_root.mkdir()
    monkeypatch.setattr(fensap_jobs, "__file__", str(tmp_path / "pkg" / "fensap_jobs.py"))

    # minimal required templates
    names = [
        "MULTISHOT.meshingSizes.scm.j2",
        "MULTISHOT.custom_remeshing.sh.j2",
        "MULTISHOT.solvercmd.j2",
        "MULTISHOT.files.j2",
        "MULTISHOT.config.par.j2",
        "MULTISHOT.fensap.par.j2",
        "MULTISHOT.drop.par.j2",
        "MULTISHOT.ice.par.j2",
        "MULTISHOT.create-2.5D-mesh.bin.j2",
        "MULTISHOT.remeshing.jou.j2",
        "MULTISHOT.fluent_config.jou.j2",
        "config.drop.j2",
        "files.drop.j2",
        "files.fensap.j2",
    ]
    for n in names:
        content = "exit 0" if n == "MULTISHOT.solvercmd.j2" else "x"
        (template_root / n).write_text(content)

    (template_root / "config.ice.j2").write_text("x")
    (template_root / "config.fensap.j2").write_text("{{ FSP_GUI_INITIAL_TYPE }}")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = "sh"
    cfg["MULTISHOT_COUNT"] = 3

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = MultiShotRunJob(project)
    job.execute()

    work = paths.solver_dir("run_MULTISHOT")
    first = (work / "config.fensap.000001").read_text().strip()
    second = (work / "config.fensap.000002").read_text().strip()
    third = (work / "config.fensap.000003").read_text().strip()
    assert first == "1"
    assert second == "2"
    assert third == "2"


def test_multishot_roughness_and_laplace(monkeypatch, tmp_path):
    template_root = tmp_path / "templates"
    template_root.mkdir()
    monkeypatch.setattr(fensap_jobs, "__file__", str(tmp_path / "pkg" / "fensap_jobs.py"))

    names = [
        "MULTISHOT.meshingSizes.scm.j2",
        "MULTISHOT.custom_remeshing.sh.j2",
        "MULTISHOT.solvercmd.j2",
        "MULTISHOT.files.j2",
        "MULTISHOT.config.par.j2",
        "MULTISHOT.fensap.par.j2",
        "MULTISHOT.drop.par.j2",
        "MULTISHOT.ice.par.j2",
        "MULTISHOT.create-2.5D-mesh.bin.j2",
        "MULTISHOT.remeshing.jou.j2",
        "MULTISHOT.fluent_config.jou.j2",
        "config.drop.j2",
        "files.drop.j2",
        "files.fensap.j2",
    ]
    for n in names:
        content = "exit 0" if n == "MULTISHOT.solvercmd.j2" else "x"
        (template_root / n).write_text(content)

    (template_root / "config.ice.j2").write_text("x")
    (template_root / "config.fensap.j2").write_text(
        "{{ FSP_GUI_ROUGHNESS_TYPE }} {{ FSP_WALL_ROUGHNESS_SWITCH }}{% if FSP_MAX_LAPLACE_ITERATIONS is defined %} {{ FSP_MAX_LAPLACE_ITERATIONS }}{% endif %}"
    )

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = "sh"
    cfg["MULTISHOT_COUNT"] = 3

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = MultiShotRunJob(project)
    job.execute()

    work = paths.solver_dir("run_MULTISHOT")
    first = (work / "config.fensap.000001").read_text().strip()
    second = (work / "config.fensap.000002").read_text().strip()
    third = (work / "config.fensap.000003").read_text().strip()
    assert first == "1 1"
    assert second == "4 2 3"
    assert third == "4 2 3"


def test_multishot_global_laplace_is_ignored_first_shot(monkeypatch, tmp_path):
    """A globally defined ``FSP_MAX_LAPLACE_ITERATIONS`` must not appear in the first shot."""
    template_root = tmp_path / "templates"
    template_root.mkdir()
    monkeypatch.setattr(fensap_jobs, "__file__", str(tmp_path / "pkg" / "fensap_jobs.py"))

    names = [
        "MULTISHOT.meshingSizes.scm.j2",
        "MULTISHOT.custom_remeshing.sh.j2",
        "MULTISHOT.solvercmd.j2",
        "MULTISHOT.files.j2",
        "MULTISHOT.config.par.j2",
        "MULTISHOT.fensap.par.j2",
        "MULTISHOT.drop.par.j2",
        "MULTISHOT.ice.par.j2",
        "MULTISHOT.create-2.5D-mesh.bin.j2",
        "MULTISHOT.remeshing.jou.j2",
        "MULTISHOT.fluent_config.jou.j2",
        "config.drop.j2",
        "files.drop.j2",
        "files.fensap.j2",
    ]
    for n in names:
        content = "exit 0" if n == "MULTISHOT.solvercmd.j2" else "x"
        (template_root / n).write_text(content)

    (template_root / "config.ice.j2").write_text("x")
    (template_root / "config.fensap.j2").write_text(
        "{{ FSP_GUI_ROUGHNESS_TYPE }} {{ FSP_WALL_ROUGHNESS_SWITCH }}{% if FSP_MAX_LAPLACE_ITERATIONS is defined %} {{ FSP_MAX_LAPLACE_ITERATIONS }}{% endif %}"
    )

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = "sh"
    cfg["MULTISHOT_COUNT"] = 2
    cfg["FSP_MAX_LAPLACE_ITERATIONS"] = 9

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = MultiShotRunJob(project)
    job.execute()

    work = paths.solver_dir("run_MULTISHOT")
    first = (work / "config.fensap.000001").read_text().strip()
    second = (work / "config.fensap.000002").read_text().strip()
    assert first == "1 1"
    assert second == "4 2 3"


def test_drop3d_run_job(tmp_path):
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
    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "FENSAP.ICE3D.custom_remeshing.sh.j2").write_text("custom")
    (template_root / "FENSAP.ICE3D.remeshing.jou.j2").write_text("jou")
    (template_root / "FENSAP.ICE3D.meshingSizes.scm.j2").write_text("scm")
    (template_root / "FENSAP.ICE3D.fluent_config.jou.j2").write_text("fluent")
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

    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "FENSAP.ICE3D.custom_remeshing.sh.j2").write_text("custom")
    (template_root / "FENSAP.ICE3D.remeshing.jou.j2").write_text("jou")
    (template_root / "FENSAP.ICE3D.meshingSizes.scm.j2").write_text("scm")
    (template_root / "FENSAP.ICE3D.fluent_config.jou.j2").write_text("fluent")
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
    rel = Path("..") / dest.relative_to(project.root)
    assert cfg["FSP_FILES_GRID"] == str(rel)
    assert cfg["ICE_GRID_FILE"] == str(rel)


def test_fluent2fensap_job_keeps_log_level(monkeypatch, tmp_path):

    from glacium.utils.logging import log

    original_level = log.level

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    exe = tmp_path / "bin" / "fluent2fensap.exe"
    exe.parent.mkdir()
    exe.write_text("")
    cfg["FLUENT2FENSAP_EXE"] = str(exe)
    cfg["PWS_GRID_PATH"] = "mesh.cas"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()

    work = paths.solver_dir("mesh")
    (work / "mesh.cas").write_text("case")

    project = Project("uid", tmp_path, cfg, paths, [])
    job = Fluent2FensapJob(project)

    def fake_run(self, cmd, *, cwd, stdin=None):
        (work / "mesh.grid").write_text("grid")

    monkeypatch.setattr(BaseEngine, "run", fake_run)

    job.execute()

    assert log.level == original_level


def test_engine_factory_create():
    """Ensure registered engines can be created by name."""

    engine = EngineFactory.create("XfoilEngine")
    assert isinstance(engine, XfoilEngine)


def test_xfoil_script_job_uses_engine_factory(monkeypatch, tmp_path):
    """Verify ``EngineFactory.create`` is used by ``XfoilScriptJob``."""

    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "test.in.j2").write_text("HELLO")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["XFOIL_BIN"] = "cat"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    class TestJob(XfoilScriptJob):
        name = "TEST"
        template = Path("test.in.j2")
        cfg_key_out = None

    called = {}

    def fake_create(name: str):
        called["name"] = name
        return XfoilEngine()

    monkeypatch.setattr(EngineFactory, "create", staticmethod(fake_create))

    project = Project("uid", tmp_path, cfg, paths, [])
    job = TestJob(project)
    job.execute()

    assert called["name"] == "XfoilEngine"


def test_fensap_script_job_uses_engine_factory(monkeypatch, tmp_path):
    """Verify ``EngineFactory.create`` is used by ``FensapScriptJob``."""

    template_root = tmp_path / "tmpl"
    template_root.mkdir()
    (template_root / "run.sh.j2").write_text("exit 0")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = "sh"

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    class TestJob(FensapScriptJob):
        name = "TEST_FSP"
        solver_dir = "fsp"
        templates = {"run.sh.j2": ".solvercmd"}

    called = {}

    def fake_create(name: str):
        called["name"] = name
        return FensapEngine()

    monkeypatch.setattr(EngineFactory, "create", staticmethod(fake_create))

    project = Project("uid", tmp_path, cfg, paths, [])
    job = TestJob(project)
    job.execute()

    assert called["name"] == "FensapEngine"

