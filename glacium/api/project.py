from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from glacium.managers.project_manager import ProjectManager
from glacium.managers.job_manager import JobManager
from glacium.models.project import Project as ModelProject

__all__ = ["Project"]


class Project:
    """High level wrapper around :class:`~glacium.models.project.Project`."""

    def __init__(self, project: ModelProject) -> None:
        super().__setattr__("_project", project)

    # ------------------------------------------------------------------
    @property
    def uid(self) -> str:
        return self._project.uid

    @property
    def root(self) -> Path:
        return self._project.root

    @property
    def config(self):
        return self._project.config

    @property
    def paths(self):
        return self._project.paths

    @property
    def jobs(self):
        return self._project.jobs

    @property
    def job_manager(self) -> JobManager:
        return self._project.job_manager  # type: ignore[return-value]

    # ------------------------------------------------------------------
    def run(self, *jobs: str) -> "Project":
        """Execute jobs via the project's :class:`JobManager`."""

        job_list: Optional[Iterable[str]]
        if jobs:
            job_list = list(jobs)
        else:
            job_list = None
        if self._project.job_manager is None:
            self._project.job_manager = JobManager(self._project)  # type: ignore[attr-defined]
        self._project.job_manager.run(job_list)  # type: ignore[arg-type]
        return self

    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        return getattr(self._project, name)

    def __setattr__(self, name: str, value):
        if name == "_project":
            super().__setattr__(name, value)
        else:
            setattr(self._project, name, value)

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, runs_root: str | Path, uid: str) -> "Project":
        """Load an existing project from ``runs_root`` by ``uid``."""

        pm = ProjectManager(Path(runs_root))
        proj = pm.load(uid)
        return cls(proj)
