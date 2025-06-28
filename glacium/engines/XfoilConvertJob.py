# glacium/engines/xfoil_convert_job.py
from pathlib import Path
from glacium.engines.PyEngine import PyEngine
from glacium.utils.convert_airfoil import xfoil_to_pointwise
from glacium.models.job import Job

class XfoilConvertJob(Job):
    name       = "XFOIL_PW_CONVERT"
    deps       = ("XFOIL_THICKEN_TE",)         # oder letzter Profil-Job
    cfg_key_out = "XFOIL_CONVERT_OUT"          # -> global_config

    def execute(self):
        cfg   = self.project.config
        paths = self.project.paths
        work  = paths.solver_dir("xfoil")

        src = Path(cfg["PWS_PROFILE2"])        # dickes Profil
        dst = Path(cfg.get(self.cfg_key_out, "profile_pw.pts"))
        cfg[self.cfg_key_out] = str(dst)

        engine = PyEngine(xfoil_to_pointwise)
        engine.run([src, dst], cwd=work,
                   expected_files=[work / dst])
