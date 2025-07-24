from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence, Callable
import sys

from glacium.models.job import Job
from glacium.engines.py_engine import PyEngine
from glacium.engines.engine_factory import EngineFactory
from glacium.utils.logging import log_call


class ScriptJob(Job, ABC):
    """Base class for jobs executing an external engine."""

    engine_name: str
    exe_key: str
    default_exe: str = ""
    solver_dir: str = ""

    @abstractmethod
    def prepare(self) -> Path:
        """Return the script file to execute."""

    def executable(self) -> str:
        return self.project.config.get(self.exe_key, self.default_exe)

    def workdir(self) -> Path:  # type: ignore[override]
        return self.project.paths.solver_dir(self.solver_dir)

    def after_run(self, work: Path) -> None:
        return None

    @log_call
    def execute(self) -> None:  # noqa: D401
        work = self.workdir()
        script = self.prepare()
        exe = self.executable()
        engine = EngineFactory.create(self.engine_name, exe)
        engine.run_script(script, work)
        self.after_run(work)


class PythonJob(Job, ABC):
    """Base job executing a Python callable via :class:`PyEngine`."""

    fn: Callable[..., None]

    @abstractmethod
    def args(self) -> Sequence[str | Path]:
        """Return arguments passed to the callable."""

    def after_run(self) -> None:
        return None

    def execute(self) -> None:  # noqa: D401
        module = sys.modules[self.__module__]
        engine_cls = getattr(module, "PyEngine", PyEngine)
        engine = engine_cls(self.fn)
        engine.run(self.args(), cwd=self.project.root)
        self.after_run()

