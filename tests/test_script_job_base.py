import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.core.base import ScriptJobBase, EngineBase
from glacium.utils.JobIndex import JobFactory
from glacium.engines.engine_factory import EngineFactory
from glacium.models.config import GlobalConfig
from glacium.models.project import Project
from glacium.managers.path_manager import PathBuilder


class MiniEngine(EngineBase):
    def __init__(self, exe: str):
        super().__init__()
        self.exe = exe
        self.called = {}

    def run_script(self, script: Path, work: Path) -> None:
        self.called["script"] = script
        self.called["work"] = work


@EngineFactory.register
class RegisteredMiniEngine(MiniEngine):
    pass


class MiniJob(ScriptJobBase):
    name = "MINI_JOB"
    engine_name = "RegisteredMiniEngine"
    exe_key = "MINI_EXE"
    solver_dir = "mini"

    def prepare(self) -> Path:
        work = self.workdir()
        script = work / "run.sh"
        work.mkdir(parents=True, exist_ok=True)
        script.write_text("echo hi")
        return script


def test_script_job_workflow(tmp_path):
    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["MINI_EXE"] = "echo"
    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    project = Project("uid", tmp_path, cfg, paths, [])

    job = MiniJob(project)
    engine = EngineFactory.create("RegisteredMiniEngine", "echo")
    job._engine = engine
    job.execute()

    assert engine.called["script"].name == "run.sh"
    assert engine.called["work"] == paths.solver_dir("mini")
    assert engine.called["script"].exists()
