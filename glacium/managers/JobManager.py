"""glacium.managers.job_manager – write‑safe jobs.yaml"""
from __future__ import annotations

import subprocess, traceback, yaml
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Iterable

from glacium.utils.logging import log
from glacium.models.job import Job, JobStatus

__all__ = ["JobManager"]


class JobManager:
    """Verwaltet Job‑Ausführung + Status‑Persistenz."""

    def __init__(self, project):
        self.project   = project
        self.paths     = project.paths
        self._jobs: Dict[str, Job] = {j.name: j for j in project.jobs}
        self._observers: List[Callable[[str, Job], None]] = []
        self._load_status()
        # ensure a jobs.yaml exists even for brand new projects
        self._save_status()

    # ------------------------------------------------------------------
    # Observer
    # ------------------------------------------------------------------
    def add_observer(self, fn: Callable[[str, Job], None]):
        self._observers.append(fn)

    def _emit(self, event: str, job: Job):
        for fn in self._observers:
            fn(event, job)

    # ------------------------------------------------------------------
    # Status‑Datei helper
    # ------------------------------------------------------------------
    def _status_file(self) -> Path:
        return self.paths.cfg_dir() / "jobs.yaml"

    def _ensure_status_parent(self):
        self._status_file().parent.mkdir(parents=True, exist_ok=True)

    def _load_status(self):
        if not self._status_file().exists():
            return
        data = yaml.safe_load(self._status_file().read_text()) or {}
        for n, s in data.items():
            if n in self._jobs:
                self._jobs[n].status = JobStatus[s]

    def _save_status(self):
        self._ensure_status_parent()
        data = {n: j.status.name for n, j in self._jobs.items()}
        yaml.dump(data, self._status_file().open("w"), sort_keys=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, jobs: Sequence[str] | None = None):
        target = set(jobs) if jobs else set(self._jobs)

        def ready(j: Job):
            return all(self._jobs[d].status is JobStatus.DONE for d in j.deps)

        while True:
            runnable = [j for j in self._jobs.values()
                        if j.name in target and j.status in {JobStatus.PENDING, JobStatus.STALE} and ready(j)]
            if not runnable:
                break
            for job in runnable:
                self._execute(job)
        self._save_status()

    # ------------------------------------------------------------------
    def _execute(self, job: Job):
        log.info(f"→ Starte Job: {job.name}")
        job.status = JobStatus.RUNNING; self._save_status(); self._emit("start", job)
        try:
            job.execute(); job.status = JobStatus.DONE; log.success(f"✓ {job.name}")
            self._emit("done", job)
        except subprocess.CalledProcessError as cpe:
            job.status = JobStatus.FAILED; log.error(f"✗ {job.name} [{cpe.returncode}]")
            self._emit("fail", job)
        except Exception:
            job.status = JobStatus.FAILED; log.error(traceback.format_exc()); self._emit("fail", job)
        finally:
            self._save_status()
