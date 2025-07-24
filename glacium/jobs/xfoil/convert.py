from __future__ import annotations

from pathlib import Path

from glacium.models.job import Job
from glacium.engines.py_engine import PyEngine
from glacium.utils.convert_airfoil import xfoil_to_pointwise
from glacium.utils.logging import log_call


class XfoilConvertJob(Job):
    name = "XFOIL_PW_CONVERT"
    deps = ("XFOIL_THICKEN_TE",)
    cfg_key_out = "XFOIL_CONVERT_OUT"

    @log_call
    def execute(self) -> None:
        cfg = self.project.config
        paths = self.project.paths
        work = paths.solver_dir("xfoil")

        src = Path(cfg["PWS_PROFILE2"])
        dst = Path(cfg["PWS_PROF_PATH"])

        cfg[self.cfg_key_out] = str(dst)

        engine = PyEngine(xfoil_to_pointwise)
        engine.run([src, dst], cwd=work, expected_files=[work / dst])
