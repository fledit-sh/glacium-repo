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
    f"Finished meshing test sequence {proj.uid} ({proj.root})"
)


drp_time_accuracy: dict[str, Any] = \
    {
    "DROP3D_DRP_GUI_CFL": 20,
    "DROP3D_FSP_DIMENSIONAL_TIME_STEP": 1000000,
    "DROP3D_FSP_GUI_CFL": 300,
    "DROP3D_FSP_GUI_DROP_MAX_TIME_STEPS_PER_CYCLE": 1,
    "DROP3D_FSP_GUI_FENSAP_MAX_TIME_STEPS_PER_CYCLE": 700,
    "DROP3D_FSP_GUI_VARIABLE_RELAXATION": 0,
    "DROP3D_FSP_INVERSE_CFL": 0.05,
    "DROP3D_FSP_MAX_NEWTON_ITERATIONS_PER_CYCLE": 1,
    "DROP3D_FSP_MAX_TIME_STEPS_PER_CYCLE": 120,
    "DROP3D_FSP_TIME_ACCURATE_SCHEME_ORDER": -1,
    "DROP3D_FSP_TOTAL_SIMULATION_TIME": 500
    }

base_jobs = [
    "FENSAP_RUN",
    "DROP3D_RUN",
    "ICE3D_RUN",
]

