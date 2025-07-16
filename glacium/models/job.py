# glacium/models/job.py
from __future__ import annotations
from enum import Enum, auto
from pathlib import Path
from typing import Sequence


class JobStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    DONE    = auto()
    FAILED  = auto()
    SKIPPED = auto()
    STALE   = auto()


class Job:
    """Basisklasse für alle konkreten Jobs (Command-Pattern)."""

    # eindeutiger Bezeichner, wird als Key im JobManager benutzt
    name: str = "BaseJob"

    # optionale Abhängigkeiten (Namen anderer Jobs)
    deps: Sequence[str] = ()

    # Register subclasses automatically ---------------------------------
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        try:  # avoid circular import during bootstrap
            from glacium.utils.JobIndex import JobFactory
        except Exception:
            return
        name = getattr(cls, "name", "BaseJob")
        if name != "BaseJob":
            JobFactory.register(cls)

    def __init__(self, project: "Project"):   # noqa: F821  (Vorwärtsreferenz)
        self.project = project
        self.status  = JobStatus.PENDING

    # ------------------------------------------------------------------
    # Template-Methode: konkrete Subklassen überschreiben execute()
    # ------------------------------------------------------------------
    def execute(self) -> None:                # noqa: D401
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Optional hook executed before a job is run
    # ------------------------------------------------------------------
    def prepare(self) -> None:
        """Prepare external files required for :meth:`execute`."""
        return None

    # ------------------------------------------------------------------
    # Kleine Helfer, die fast jeder Job braucht
    # ------------------------------------------------------------------
    def workdir(self) -> Path:
        return self.project.paths.runs_dir() / self.name.lower()


class UnavailableJob(Job):
    """Placeholder for jobs that could not be imported."""

    available = False

    def __init__(self, project: "Project", job_name: str, reason: str | None = None):
        super().__init__(project)
        self.name = job_name
        self.reason = reason or "missing dependency"

    def execute(self) -> None:
        raise RuntimeError(f"Job '{self.name}' unavailable: {self.reason}")

