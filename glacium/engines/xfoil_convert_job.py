# glacium/engines/xfoil_convert_job.py
from pathlib import Path
from glacium.engines.py_engine import PyEngine
from glacium.utils.convert_airfoil import xfoil_to_pointwise
from glacium.models.job import Job
from glacium.utils.logging import log_call

class XfoilConvertJob(Job):
    name       = "XFOIL_PW_CONVERT"
    deps       = ("XFOIL_THICKEN_TE",)         # oder letzter Profil-Job
    cfg_key_out = "XFOIL_CONVERT_OUT"          # -> global_config

    @log_call
    def execute(self):
        cfg   = self.project.config
        paths = self.project.paths
        work  = paths.solver_dir("xfoil")

        src = Path(cfg["PWS_PROFILE2"])        # dickes Profil
        dst = Path(cfg["PWS_PROF_PATH"])

        cfg[self.cfg_key_out] = str(dst)

        engine = PyEngine(xfoil_to_pointwise)
        engine.run([src, dst], cwd=work,
                   expected_files=[work / dst])
