import sys
import types
import importlib.machinery
import importlib.util
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Avoid executing glacium.__init__ (pulls heavy optional deps) -----------------
pkg_root = Path(__file__).resolve().parents[1] / "glacium"
glacium_stub = types.ModuleType("glacium")
glacium_stub.__path__ = [str(pkg_root)]
sys.modules.setdefault("glacium", glacium_stub)

from glacium.managers.job_manager import JobManager
from glacium.models.job import Job, JobStatus
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project

loader = importlib.machinery.SourceFileLoader(
    "glacium.jobs.postprocess_jobs", str(pkg_root / "jobs" / "postprocess_jobs.py")
)
spec = importlib.util.spec_from_loader(loader.name, loader)
postprocess_jobs = importlib.util.module_from_spec(spec)
loader.exec_module(postprocess_jobs)
PostprocessSingleFensapJob = postprocess_jobs.PostprocessSingleFensapJob


def _project(root: Path) -> Project:
    cfg = GlobalConfig(project_uid="uid", base_dir=root)
    paths = PathBuilder(root).build()
    paths.ensure()
    return Project("uid", root, cfg, paths, [])


def test_postprocess_single_execution_order(tmp_path, monkeypatch):
    executed: list[str] = []
    orig_run = JobManager.run

    def recording_run(self, jobs=None, include_failed=False):  # type: ignore[override]
        orig_execute = self._execute

        def record(job):
            executed.append(job.name)
            job.status = JobStatus.DONE

        self._execute = record  # type: ignore[assignment]
        try:
            return orig_run(self, jobs, include_failed)
        finally:
            self._execute = orig_execute  # type: ignore[assignment]

    monkeypatch.setattr(JobManager, "run", recording_run)

    # FENSAP only project
    root1 = tmp_path / "p1"
    proj1 = _project(root1)

    class Fensap(Job):
        name = "FENSAP_RUN"
        deps = ()

        def execute(self):
            pass

    proj1.jobs = [Fensap(proj1)]
    proj1.jobs.append(PostprocessSingleFensapJob(proj1))
    jm1 = JobManager(proj1)
    jm1.run()
    assert executed == ["FENSAP_RUN", "POSTPROCESS_SINGLE_FENSAP"]

    # Multi-run project
    executed.clear()
    root2 = tmp_path / "p2"
    proj2 = _project(root2)

    class Drop(Job):
        name = "DROP3D_RUN"
        deps = ("FENSAP_RUN",)

        def execute(self):
            pass

    class Ice(Job):
        name = "ICE3D_RUN"
        deps = ("DROP3D_RUN",)

        def execute(self):
            pass

    f = Fensap(proj2)
    d = Drop(proj2)
    i = Ice(proj2)
    proj2.jobs = [f, d, i]
    proj2.jobs.append(PostprocessSingleFensapJob(proj2))
    jm2 = JobManager(proj2)
    jm2.run()
    assert executed == [
        "FENSAP_RUN",
        "DROP3D_RUN",
        "ICE3D_RUN",
        "POSTPROCESS_SINGLE_FENSAP",
    ]
    assert executed[-1] == "POSTPROCESS_SINGLE_FENSAP"
    assert executed[-2] == "ICE3D_RUN"
