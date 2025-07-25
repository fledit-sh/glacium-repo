from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence, Callable, Optional, IO
from enum import Enum, auto
from abc import ABC, abstractmethod
import subprocess

class JobStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    DONE = auto()
    FAILED = auto()
    SKIPPED = auto()
    STALE = auto()

import sys

from glacium.utils.logging import log, log_call



@dataclass
class JobBase(ABC):
    """Minimal abstract job base class."""

    project: "Project"
    name: str = "BaseJob"
    deps: Sequence[str] = field(default_factory=tuple)
    status: JobStatus = field(default=JobStatus.PENDING)

    def prepare(self) -> Path | None:
        """Optional hook executed before :meth:`execute`."""
        return None

    @abstractmethod
    def execute(self) -> None:
        """Run the job."""

    def workdir(self) -> Path:
        """Return the working directory for this job."""
        return self.project.paths.runs_dir() / self.name.lower()


@dataclass
class EngineBase(ABC):
    """Abstract base for external process wrappers."""

    timeout: int | None = None

    @log_call
    def run(
        self,
        cmd: Sequence[str],
        *,
        cwd: Path,
        stdin: Optional[IO[str]] = None,
    ) -> None:
        """Execute ``cmd`` inside ``cwd`` with optional timeout."""
        cmd_str = " ".join(cmd)
        log.info(f"RUN: {cmd_str}")
        try:
            subprocess.run(
                cmd,
                stdin=stdin,
                cwd=cwd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                timeout=self.timeout,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Executable not found: {cmd[0]}") from exc

    def run_script(self, script: Path, work: Path) -> None:
        """Optional helper executing ``script`` in ``work``."""
        self.run([str(script)], cwd=work)


class ScriptJobBase(JobBase, ABC):
    """Job running an external engine with a script file."""

    engine_name: str
    exe_key: str
    default_exe: str = ""
    solver_dir: str = ""

    def __init__(
        self,
        project: "Project",
        engine: Optional[EngineBase | Callable[[str], EngineBase]] = None,
    ) -> None:
        super().__init__(project)
        self._engine = engine

    @abstractmethod
    def prepare(self) -> Path:
        """Return the script to execute."""

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
        if callable(self._engine):
            engine = self._engine(exe)
        elif isinstance(self._engine, EngineBase):
            engine = self._engine
        else:
            from glacium.engines.engine_factory import EngineFactory

            engine = EngineFactory.create(self.engine_name, exe)
        engine.run_script(script, work)
        self.after_run(work)


class PythonJobBase(JobBase, ABC):
    """Job executing a Python callable via :class:`PyEngine`."""

    fn: Callable[..., None]

    @abstractmethod
    def args(self) -> Sequence[str | Path]:
        """Return arguments passed to the callable."""

    def after_run(self) -> None:
        return None

    def execute(self) -> None:  # noqa: D401
        from glacium.engines.py_engine import PyEngine

        module = sys.modules[self.__module__]
        engine_cls = getattr(module, "PyEngine", PyEngine)
        engine = engine_cls(self.fn)
        engine.run(self.args(), cwd=self.project.root)
        self.after_run()

