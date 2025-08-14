import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Avoid executing glacium.__init__ (pulls heavy optional deps)
pkg_root = Path(__file__).resolve().parents[1] / "glacium"
glacium_stub = types.ModuleType("glacium")
glacium_stub.__path__ = [str(pkg_root)]
sys.modules.setdefault("glacium", glacium_stub)

from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project
from glacium.managers.job_manager import JobManager
from glacium.models.job import Job


def _project(root: Path) -> Project:
    cfg = GlobalConfig(project_uid="uid", base_dir=root)
    paths = PathBuilder(root).build()
    paths.ensure()
    return Project("uid", root, cfg, paths, [])


def test_scheduler_picks_newly_ready_jobs_before_unrelated(tmp_path):
    executed: list[str] = []
    project = _project(tmp_path)

    class A(Job):
        name = "A"
        deps = ()

        def execute(self):
            executed.append(self.name)

    class B(Job):
        name = "B"
        deps = ("A",)

        def execute(self):
            executed.append(self.name)

    class D(Job):
        name = "D"
        deps = ("B",)

        def execute(self):
            executed.append(self.name)

    class C(Job):
        name = "C"
        deps = ("A",)

        def execute(self):
            executed.append(self.name)

    project.jobs = [A(project), B(project), D(project), C(project)]

    jm = JobManager(project)
    jm.run()

    assert executed == ["A", "B", "D", "C"]
