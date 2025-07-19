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

    # ------------------------------------------------------------------
    def add_job(self, name: str) -> list[str]:
        """Append ``name`` and its missing dependencies.

        The project configuration is updated and ``jobs.yaml`` is
        persisted.  The return value lists all job names that were
        actually appended to the project in dependency order.
        """

        proj = self._project
        if proj.job_manager is None:
            proj.job_manager = JobManager(proj)  # type: ignore[attr-defined]

        from glacium.managers.recipe_manager import RecipeManager
        from glacium.managers.config_manager import ConfigManager
        from glacium.utils import list_jobs
        from glacium.utils.JobIndex import JobFactory

        if proj.config.recipe == "CUSTOM":
            recipe_jobs = {}
        else:
            recipe = RecipeManager.create(proj.config.recipe)
            recipe_jobs = {j.name: j for j in recipe.build(proj)}

        if name.isdigit():
            idx = int(name) - 1
            all_jobs = list_jobs()
            if idx < 0 or idx >= len(all_jobs):
                raise ValueError("invalid job number")
            target = all_jobs[idx]
        else:
            target = name.upper()

        added: list[str] = []

        def add_with_deps(jname: str) -> None:
            if jname in proj.job_manager._jobs or jname in added:
                return
            job = recipe_jobs.get(jname)
            if job is None:
                if JobFactory.get(jname) is None:
                    raise KeyError(f"Job '{jname}' not known")
                job = JobFactory.create(jname, proj)
            for dep in getattr(job, "deps", ()):
                add_with_deps(dep)
            proj.jobs.append(job)
            proj.job_manager._jobs[jname] = job
            try:
                job.prepare()
            except Exception:
                pass
            added.append(jname)

        add_with_deps(target)

        proj.job_manager._save_status()

        proj.config.recipe = "CUSTOM"
        cfg_mgr = ConfigManager(proj.paths)
        cfg = cfg_mgr.load_global()
        cfg.recipe = "CUSTOM"
        cfg_mgr.dump_global()
        cfg_mgr.set("RECIPE", "CUSTOM")

        return added
