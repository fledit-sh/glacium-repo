"""Helper for discovering implemented Job classes."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable, Dict, Optional

from glacium.models.job import Job

# packages containing job implementations
_PACKAGES: Iterable[str] = ["glacium.engines", "glacium.recipes"]

# names of jobs not shown in public listings
_EXCLUDE: set[str] = {"FENSAP_RUN"}


def _discover() -> None:
    """Import all modules from known packages to populate Job subclasses."""
    for pkg_name in _PACKAGES:
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


def list_jobs() -> list[str]:
    """Return a sorted list of all implemented job names."""
    _discover()

    found: set[str] = set()

    def _collect(cls: type[Job]) -> None:
        for sub in cls.__subclasses__():
            name = getattr(sub, "name", "BaseJob")
            if name != "BaseJob":
                found.add(name)
            _collect(sub)

    _collect(Job)
    return sorted(n for n in found if n not in _EXCLUDE)


def _collect_map() -> Dict[str, type[Job]]:
    mapping: Dict[str, type[Job]] = {}

    def _collect(cls: type[Job]) -> None:
        for sub in cls.__subclasses__():
            name = getattr(sub, "name", "BaseJob")
            if name != "BaseJob":
                mapping[name] = sub
            _collect(sub)

    _collect(Job)
    return mapping


def get_job_class(name: str) -> Optional[type[Job]]:
    """Return the Job subclass with ``name`` if available."""

    _discover()
    return _collect_map().get(name)


def create_job(name: str, project) -> Job:
    """Instantiate the Job with ``name`` for ``project``."""

    cls = get_job_class(name)
    if cls is None:
        raise KeyError(f"Job '{name}' nicht bekannt.")
    return cls(project)
