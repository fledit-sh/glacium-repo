"""Execute jobs and persist their state.

The manager keeps a ``jobs.yaml`` file up to date while running the jobs of a
project.  It is safe to call repeatedly and supports simple observer hooks.

Example
-------
>>> jm = JobManager(project)
>>> jm.run()  # executes jobs defined in the project
"""
from __future__ import annotations

import subprocess, traceback, yaml
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Iterable

from glacium.utils.logging import log
from datetime import datetime, UTC
from glacium.models.job import Job, JobStatus

__all__ = ["JobManager"]


class JobManager:
    """Manage job execution and store their status."""

    def __init__(self, project):
        """Initialise the manager and load persisted job status.

        Parameters
        ----------
        project:
            Project object containing job definitions and paths.
        """

        self.project = project
        self.paths = project.paths
        self._jobs: Dict[str, Job] = {j.name: j for j in project.jobs}
        self._observers: List[Callable[[str, Job], None]] = []
        self._time_log = self.paths.root / "job_times.csv"
        self._load_status()
        # ensure a jobs.yaml exists even for brand new projects
        self._save_status()

    # ------------------------------------------------------------------
    # Observer
    # ------------------------------------------------------------------
    def add_observer(self, fn: Callable[[str, Job], None]):
        """Register ``fn`` to be notified on job events."""

        self._observers.append(fn)

    def _emit(self, event: str, job: Job):
        """Notify observers about ``event`` for ``job``."""

        for fn in self._observers:
            fn(event, job)

    # ------------------------------------------------------------------
    # Status‑Datei helper
    # ------------------------------------------------------------------
    def _status_file(self) -> Path:
        """Return path to the YAML file storing job status."""

        return self.paths.cfg_dir() / "jobs.yaml"

    def _ensure_status_parent(self):
        """Make sure the status file directory exists."""

        self._status_file().parent.mkdir(parents=True, exist_ok=True)

    def _load_status(self):
        """Load job status information from disk if available."""

        if not self._status_file().exists():
            return
        data = yaml.safe_load(self._status_file().read_text()) or {}
        for n, s in data.items():
            if n in self._jobs:
                self._jobs[n].status = JobStatus[s]

    def _save_status(self):
        """Persist the current job status map to disk."""

        self._ensure_status_parent()
        data = {j.name: j.status.name for j in self.project.jobs}
        with self._status_file().open("w") as fh:
            yaml.dump(data, fh, sort_keys=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, jobs: Sequence[str] | None = None, include_failed: bool = False):
        """Execute jobs in dependency order.

        Parameters
        ----------
        jobs:
            Optional sequence of job names to run. If ``None`` all jobs are
            considered.
        include_failed:
            If ``True``, also re-run jobs with status ``FAILED``.
        """

        target = set(jobs) if jobs else set(self._jobs)

        def ready(j: Job) -> bool:
            """Return ``True`` if all dependencies of ``j`` are done."""

            for d in j.deps:
                dep = self._jobs.get(d)
                if dep is None:
                    log.warning(f"Dependency '{d}' for job '{j.name}' missing")
                    return False
                if dep.status is not JobStatus.DONE:
                    return False
            return True

        while True:
            runnable_statuses = {JobStatus.PENDING, JobStatus.STALE}
            if include_failed:
                runnable_statuses.add(JobStatus.FAILED)
            runnable = [j for j in self._jobs.values()
                        if j.name in target and j.status in runnable_statuses and ready(j)]
            if not runnable:
                break
            for job in runnable:
                self._execute(job)
        self._save_status()

    # ------------------------------------------------------------------
    def reset_jobs(self, names: Iterable[str]) -> None:
        """Set listed jobs to ``PENDING`` if they are not currently running."""

        for name in names:
            job = self._jobs.get(name)
            if job is None:
                continue
            if job.status is not JobStatus.RUNNING:
                job.status = JobStatus.PENDING
        self._save_status()

    # ------------------------------------------------------------------
    def _log_time(self, name: str, start: datetime, end: datetime) -> None:
        """Append timing information for ``name`` to ``job_times.csv``."""

        self._time_log.parent.mkdir(parents=True, exist_ok=True)
        duration = (end - start).total_seconds()
        write_header = not self._time_log.exists()
        with self._time_log.open("a", encoding="utf-8") as fh:
            if write_header:
                fh.write("job,start,end,duration_s\n")
            fh.write(f"{name},{start.isoformat()},{end.isoformat()},{duration:.3f}\n")

    # ------------------------------------------------------------------
    def _execute(self, job: Job):
        """Run a single job and update its status."""

        log.info(f"Starting job: {job.name}")
        start_dt = datetime.now(UTC)
        job.status = JobStatus.RUNNING; self._save_status(); self._emit("start", job)
        try:
            job.execute(); job.status = JobStatus.DONE; log.success(f"DONE: {job.name}")
            self._emit("done", job)
        except subprocess.CalledProcessError as cpe:
            job.status = JobStatus.FAILED; log.error(f"FAILED: {job.name} [{cpe.returncode}]")
            self._emit("fail", job)
        except Exception:
            job.status = JobStatus.FAILED; log.error(traceback.format_exc()); self._emit("fail", job)
        finally:
            end_dt = datetime.now(UTC)
            self._log_time(job.name, start_dt, end_dt)
            self._save_status()

