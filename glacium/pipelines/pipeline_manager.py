"""Base class and registry for pipeline implementations."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Type

from glacium.utils.logging import log
from glacium.managers.project_manager import ProjectManager


class BasePipeline:
    """Base class for all pipelines."""

    name: str = "base"
    description: str = "(no description)"

    def run(self, pm: ProjectManager, **kwargs):  # noqa: D401
        """Execute the pipeline using ``pm``."""

        raise NotImplementedError


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
