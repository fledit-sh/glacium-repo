"""Domain models representing job state."""
from __future__ import annotations

from pathlib import Path
from abc import abstractmethod
from glacium.core.base import JobBase, JobStatus
__all__ = ["JobStatus", "Job", "UnavailableJob"]



class Job(JobBase):
    """Base class for concrete jobs following the Command pattern."""

    # Register subclasses automatically ---------------------------------
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        try:  # avoid circular import during bootstrap
            from glacium.utils.job_index import JobFactory
        except Exception:
            return
        name = getattr(cls, "name", "BaseJob")
        if name != "BaseJob":
            JobFactory.register(cls)

    def __init__(self, project: "Project") -> None:
        super().__init__(project)

    @abstractmethod
    def execute(self) -> None:  # noqa: D401
        """Run the job."""



class UnavailableJob(Job):
    """Placeholder for jobs that could not be imported."""

    available = False

    def __init__(self, project: "Project", job_name: str, reason: str | None = None):
        super().__init__(project)
        self.name = job_name
        self.reason = reason or "missing dependency"

    def execute(self) -> None:
        raise RuntimeError(f"Job '{self.name}' unavailable: {self.reason}")
