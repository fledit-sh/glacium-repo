"""Helper for discovering implemented Job classes."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable

from glacium.models.job import Job

# packages containing job implementations
_PACKAGES: Iterable[str] = ["glacium.engines", "glacium.recipes"]


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
    return sorted(found)
