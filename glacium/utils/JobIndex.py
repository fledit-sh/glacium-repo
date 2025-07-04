"""Helper for discovering implemented Job classes."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable, Dict, Optional, Type

from glacium.models.job import Job
from glacium.utils.logging import log

__all__ = ["JobFactory", "list_jobs", "get_job_class", "create_job"]


class JobFactory:
    """Registry and factory for :class:`Job` classes."""

    _jobs: Dict[str, Type[Job]] | None = None
    _loaded: bool = False
    _PACKAGES: Iterable[str] = ["glacium.jobs", "glacium.engines", "glacium.recipes"]

    # ------------------------------------------------------------------
    @classmethod
    def register(cls, job_cls: Type[Job]) -> Type[Job]:
        """Register ``job_cls`` under its ``name`` attribute."""
        if cls._jobs is None:
            cls._jobs = {}
        name = getattr(job_cls, "name", "BaseJob")
        if name == "BaseJob":
            return job_cls
        if name in cls._jobs:  # type: ignore[arg-type]
            log.warning(f"Job '{name}' wird überschrieben.")
        cls._jobs[name] = job_cls  # type: ignore[index]
        return job_cls

    # ------------------------------------------------------------------
    @classmethod
    def create(cls, name: str, project) -> Job:
        """Instantiate the registered job ``name`` for ``project``."""

        cls._load()
        if name not in cls._jobs:  # type: ignore[arg-type]
            raise KeyError(f"Job '{name}' nicht bekannt.")
        return cls._jobs[name](project)  # type: ignore[index]

    # ------------------------------------------------------------------
    @classmethod
    def list(cls) -> list[str]:
        """Return all registered job names."""

        cls._load()
        return sorted(cls._jobs)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    @classmethod
    def get(cls, name: str) -> Optional[Type[Job]]:
        """Return the registered class for ``name`` if available."""

        cls._load()
        return cls._jobs.get(name)  # type: ignore[return-value]

    # ------------------------------------------------------------------
    @classmethod
    def _load(cls) -> None:
        if cls._jobs is None:
            cls._jobs = {}
        if not cls._loaded:
            cls._discover()
            cls._loaded = True

    @classmethod
    def _discover(cls) -> None:
        """Import all modules from known packages to populate registry."""

        for pkg_name in cls._PACKAGES:
            try:
                pkg = importlib.import_module(pkg_name)
            except ModuleNotFoundError:
                continue
            for mod in pkgutil.walk_packages(pkg.__path__, pkg_name + "."):
                try:
                    importlib.import_module(mod.name)
                except Exception:
                    # ignore faulty modules during discovery
                    pass


# Backwards compatible helper functions --------------------------------------
def list_jobs() -> list[str]:
    return JobFactory.list()


def get_job_class(name: str) -> Optional[Type[Job]]:
    return JobFactory.get(name)


def create_job(name: str, project) -> Job:
    return JobFactory.create(name, project)
