import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project
from glacium.managers.job_manager import JobManager
from glacium.models.job import Job, JobStatus


def test_run_reruns_failed_jobs(tmp_path):
    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    paths = PathBuilder(tmp_path).build()
    paths.ensure()

    project = Project("uid", tmp_path, cfg, paths, [])

    executed = []

    class DummyJob(Job):
        name = "DUMMY"
        deps = ()

        def execute(self):
            executed.append("x")

    job = DummyJob(project)
    job.status = JobStatus.FAILED
    project.jobs = [job]

    jm = JobManager(project)

    jm.run()
    assert executed == []
    assert job.status is JobStatus.FAILED

    jm.run(include_failed=True)
    assert executed == ["x"]
    assert job.status is JobStatus.DONE
