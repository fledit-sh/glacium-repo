"""Base class and registry for pipeline implementations."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Type, Sequence

import yaml

from glacium.utils.JobIndex import JobFactory
from glacium.managers.job_manager import JobManager
from glacium.utils.convergence import project_cl_cd_stats
from glacium.pipelines.step import PipelineStep

from glacium.utils.logging import log
from glacium.managers.project_manager import ProjectManager


class BasePipeline:
    """Base class for all pipelines."""

    name: str = "base"
    description: str = "(no description)"

    def run(self, pm: ProjectManager, steps: Sequence[PipelineStep]):  # noqa: D401
        """Execute ``steps`` using ``pm``.

        Parameters
        ----------
        pm:
            Project manager used to create and load projects.
        steps:
            Ordered list of :class:`PipelineStep` objects describing the
            workflow.

        Returns
        -------
        tuple[list[str], list[tuple[str, float, float, float, float]]]
            Project UIDs and solver statistics for each step.
        """

        default_airfoil = Path(__file__).resolve().parents[1] / "data" / "AH63K127.dat"

        uids: list[str] = []
        stats: list[tuple[str, float, float, float, float]] = []

        for idx, step in enumerate(steps, 1):
            proj_name = f"{self.name}_{idx}"
            project = pm.create(proj_name, step.recipe_name, default_airfoil)
            uids.append(project.uid)

            if step.case_params:
                case_file = project.root / "case.yaml"
                case = yaml.safe_load(case_file.read_text()) or {}
                case.update(step.case_params)
                case_file.write_text(yaml.safe_dump(case, sort_keys=False))

            jm = project.job_manager or JobManager(project)
            jm.run()

            if step.post_jobs:
                for name in step.post_jobs:
                    project.jobs.append(JobFactory.create(name, project))
                project.job_manager = JobManager(project)
                project.job_manager.run(step.post_jobs)

            report_dir = project.root / "run_FENSAP"
            if report_dir.exists():
                stats.append((project.uid, *project_cl_cd_stats(report_dir)))

        return uids, stats


class PipelineManager:
    _pipelines: Dict[str, Type[BasePipeline]] | None = None

    @classmethod
    def create(cls, name: str) -> BasePipeline:
        """Instantiate the pipeline registered as ``name``."""

        cls._load()
        if name not in cls._pipelines:  # type: ignore[arg-type]
            raise KeyError(f"Pipeline '{name}' nicht registriert.")
        return cls._pipelines[name]()  # type: ignore[index]

    @classmethod
    def list(cls) -> List[str]:
        """Return the names of all registered pipelines."""

        cls._load()
        return sorted(cls._pipelines)  # type: ignore[arg-type]

    @classmethod
    def register(cls, pipe_cls: Type[BasePipeline]):
        """Class decorator to register ``pipe_cls``."""

        cls._load()
        if pipe_cls.name in cls._pipelines:  # type: ignore
            log.warning(f"Pipeline '{pipe_cls.name}' wird überschrieben.")
        cls._pipelines[pipe_cls.name] = pipe_cls  # type: ignore[index]
        return pipe_cls

    # Internal -------------------------------------------------------------
    @classmethod
    def _load(cls):
        """Populate the internal pipeline registry if empty."""

        if cls._pipelines is not None:
            return
        cls._pipelines = {}
        cls._discover("glacium.pipelines")
        log.debug(f"Pipelines: {', '.join(cls._pipelines)}")  # type: ignore[arg-type]

    @classmethod
    def _discover(cls, pkg_name: str):
        """Import all submodules from ``pkg_name`` to populate registry."""

        try:
            pkg = importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            return
        pkg_path = Path(pkg.__file__).parent
        for mod in pkgutil.iter_modules([str(pkg_path)]):
            importlib.import_module(f"{pkg_name}.{mod.name}")
