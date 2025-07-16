from __future__ import annotations

from pathlib import Path
from typing import Iterable, Dict, Any

from glacium.managers.project_manager import ProjectManager
from glacium.managers.config_manager import ConfigManager
from glacium.managers.job_manager import JobManager
from glacium.utils.JobIndex import JobFactory
from glacium.utils.logging import log


class Run:
    """Fluent helper to configure and create a project."""

    def __init__(self, runs_root: str | Path) -> None:
        self.runs_root = Path(runs_root)
        self._name = "project"
        self._airfoil: Path = Path(__file__).resolve().parents[1] / "data" / "AH63K127.dat"
        self._params: Dict[str, Any] = {"RECIPE": "prep"}
        self._jobs: list[str] = []
        self.tags: list[str] = []

    # ------------------------------------------------------------------
    def name(self, value: str) -> "Run":
        self._name = value
        return self

    def select_airfoil(self, airfoil: str | Path) -> "Run":
        self._airfoil = Path(airfoil)
        return self

    def set(self, key: str, value: Any) -> "Run":
        self._params[key.upper()] = value
        return self

    def set_bulk(self, data: Dict[str, Any]) -> "Run":
        for k, v in data.items():
            self.set(k, v)
        return self

    def add_job(self, name: str) -> "Run":
        self._jobs.append(name)
        return self

    def jobs(self, names: Iterable[str]) -> "Run":
        for n in names:
            self.add_job(n)
        return self

    def tag(self, label: str) -> "Run":
        self.tags.append(label)
        return self

    def clone(self) -> "Run":
        other = Run(self.runs_root)
        other._name = self._name
        other._airfoil = self._airfoil
        other._params = dict(self._params)
        other._jobs = list(self._jobs)
        other.tags = list(self.tags)
        return other

    # ------------------------------------------------------------------
    def preview(self) -> "Run":
        log.info(f"Project name: {self._name}")
        log.info(f"Airfoil: {self._airfoil}")
        if self._params:
            log.info("Parameters:")
            for k, v in self._params.items():
                log.info(f"  {k} = {v}")
        if self._jobs:
            log.info("Jobs: " + ", ".join(self._jobs))
        if self.tags:
            log.info("Tags: " + ", ".join(self.tags))
        return self

    # ------------------------------------------------------------------
    def create(self):
        recipe = str(self._params.get("RECIPE", "prep"))
        multishots = self._params.get("MULTISHOT_COUNT")
        pm = ProjectManager(self.runs_root)
        project = pm.create(self._name, recipe, self._airfoil, multishots=multishots)

        cfg_mgr = ConfigManager(project.paths)
        for k, v in self._params.items():
            if k in {"RECIPE", "PROJECT_NAME", "MULTISHOT_COUNT"}:
                continue
            cfg_mgr.set(k, v)

        for name in self._jobs:
            try:
                job = JobFactory.create(name, project)
                project.jobs.append(job)
                try:
                    job.prepare()
                except Exception:
                    log.warning(f"Failed to prepare job {name}")
            except Exception as err:
                log.error(f"{name}: {err}")
        project.job_manager = JobManager(project)
        return project
