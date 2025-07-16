"""Support for running FENSAP via templated shell scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping
import sys

import yaml

from glacium.utils.logging import log, log_call
from glacium.models.job import Job
from glacium.managers.template_manager import TemplateManager
from .base_engine import BaseEngine
from .engine_factory import EngineFactory


@EngineFactory.register
class FensapEngine(BaseEngine):
    """Execute ``.solvercmd`` files via ``nti_sh.exe``."""

    def run_script(self, exe: str, script: Path, work: Path) -> None:
        """Run ``script`` using ``exe`` inside ``work`` directory."""

        log.info(f"RUN: {exe} {script.name}")
        self.run([exe, str(script)], cwd=work)


__all__: Iterable[str] = [
    "FensapEngine",
    "FensapScriptJob",
]


class FensapScriptJob(Job):
    """Render FENSAP input files and execute the solver."""

    # Mapping of template -> output filename relative to the solver dir
    templates: Mapping[str | Path, str] = {}
    # Name of the solver work directory
    solver_dir: str = ""
    # Optional batch directory containing more templates
    batch_dir: Path | None = None
    deps: tuple[str, ...] = ()

    _DEFAULT_EXE = (
        r"C:\\Program Files\\ANSYS Inc\\v251\\fensapice\\bin\\nti_sh.exe"
    )

    # ------------------------------------------------------------------
    def prepare(self):
        """Render all templates into the solver directory."""
        paths = self.project.paths
        work = paths.solver_dir(self.solver_dir)
        ctx = self._context()
        tm = TemplateManager()

        module_root = Path(sys.modules[self.__class__.__module__].__file__).resolve().parents[1]
        template_root = module_root / "templates"

        if self.batch_dir:
            batch_root = template_root / self.batch_dir
            for p in batch_root.glob("*.j2"):
                tm.render_to_file(
                    p.relative_to(template_root),
                    ctx,
                    work / p.with_suffix("").name,
                )

        for tpl, dest in self.templates.items():
            tm.render_to_file(tpl, ctx, work / dest)

        return work / ".solvercmd"

    def _context(self) -> dict:
        from glacium.utils.default_paths import global_default_config

        defaults_file = global_default_config()
        defaults = yaml.safe_load(defaults_file.read_text()) if defaults_file.exists() else {}
        cfg = self.project.config
        return {**defaults, **cfg.extras}

    @log_call
    def execute(self) -> None:  # noqa: D401
        cfg = self.project.config
        paths = self.project.paths
        work = paths.solver_dir(self.solver_dir)

        self.prepare()

        exe = cfg.get("FENSAP_EXE", self._DEFAULT_EXE)
        engine = EngineFactory.create("FensapEngine")
        engine.run_script(exe, work / ".solvercmd", work)



