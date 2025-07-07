"""Job converting Fluent case files for FENSAP."""

from __future__ import annotations

import shutil
from pathlib import Path

from glacium.models.job import Job
from glacium.engines.base_engine import BaseEngine
from glacium.utils.logging import log, log_call
from .engine_factory import EngineFactory
__all__ = ["Fluent2FensapJob"]


class Fluent2FensapJob(Job):
    """Run ``fluent2fensap.exe`` to produce a ``.grid`` file."""

    name = "FLUENT2FENSAP"
    deps: tuple[str, ...] = ("XFOIL_THICKEN_TE",)

    _DEFAULT_EXE = (
        r"C:/Program Files/ANSYS Inc/v251/fensapice/bin/fluent2fensap.exe"
    )

    @log_call
    def execute(self) -> None:  # noqa: D401
        cfg = self.project.config
        paths = self.project.paths
        work = paths.solver_dir("mesh")

        cas_path = Path(cfg["PWS_GRID_PATH"])
        cas_name = cas_path.name
        cas_stem = cas_path.stem

        exe = cfg.get("FLUENT2FENSAP_EXE", self._DEFAULT_EXE)

        exe_path = Path(exe)
        log.debug(f"Using fluent2fensap executable: {exe_path}")
        if not exe_path.exists():
            raise FileNotFoundError(f"fluent2fensap executable not found: {exe_path}")
        cas_file = work / cas_name
        if not cas_file.exists():
            raise FileNotFoundError(f"case file not found: {cas_file}")

        engine = EngineFactory.create("BaseEngine")
        engine.run([exe, cas_name, cas_stem], cwd=work)

        produced = work / f"{cas_stem}.grid"
        dest = paths.mesh_dir() / produced.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(produced), dest)

        rel = Path("..") / dest.relative_to(self.project.root)
        cfg["FSP_FILES_GRID"] = str(rel)
        if "ICE_GRID_FILE" in cfg:
            cfg["ICE_GRID_FILE"] = str(rel)
