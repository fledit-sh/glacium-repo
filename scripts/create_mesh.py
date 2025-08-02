from pathlib import Path
from typing import Any

from glacium.api import Project
from glacium.utils.logging import log


base_dir = ""
root = Path(base_dir) / "StudyTest"
base = Project(root).name("grid")

defaults: dict[str, Any] = {
    "CASE_CHARACTERISTIC_LENGTH": 0.431,
    "CASE_VELOCITY": 20,
    "CASE_ALTITUDE": 100,
    "CASE_TEMPERATURE": 263.15,
    "CASE_AOA": 0,
    "CASE_YPLUS": 0.3,
}

for key, value in defaults.items():
    base.set(key, value)

mesh_jobs = [
    "XFOIL_REFINE",
    "XFOIL_THICKEN_TE",
    "XFOIL_PW_CONVERT",
    "POINTWISE_GCI",
    "FLUENT2FENSAP",
]

# builder.set("PWS_REFINEMENT", factor)
for job in mesh_jobs:
    base.add_job(job)


proj = base.create()
proj.run()
log.info(
    f"Finished test sequence {proj.uid} ({proj.root})"
)





