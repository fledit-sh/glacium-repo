from pathlib import Path

import glacium as glc
from glacium.api import Project


def main():
    # create projects below ./runs in the current directory

    base_project = (
        Project("Project01")
        .name("Preprocessing")
        .create()
    )

    base_project.set("CASE_CHARACTERISTIC_LENGTH", 0.431)
    base_project.set("CASE_VELOCITY", 50)
    base_project.set("CASE_ALTITUDE", 0)
    base_project.set("CASE_TEMPERATURE", 263.15)
    base_project.set("CASE_AOA", 0)
    base_project.set("CASE_YPLUS", 0.3)
    base_project.set("PWS_REFINEMENT", 8)

    # Job definitions
    base_project.add_job("XFOIL_REFINE")
    base_project.add_job("XFOIL_THICKEN_TE")
    base_project.add_job("XFOIL_PW_CONVERT")

    prj_xgrid = base_project.clone()
    prj_xgrid.name("X Grid")
    prj_xgrid.set("PWS_REFINEMENT", 0.25)
    prj_xgrid.add_job("POINTWISE_GCI")
    prj_xgrid.add_job("FENSAP_RUN")

    prj_fgrid = base_project.clone()
    prj_fgrid.name("F Grid")
    prj_fgrid.set("PWS_REFINEMENT", 0.5)
    prj_fgrid.add_job("POINTWISE_GCI")
    prj_fgrid.add_job("FENSAP_RUN")

    prj_mgrid = base_project.clone()
    prj_mgrid.name("M Grid")
    prj_mgrid.set("PWS_REFINEMENT", 1)
    prj_mgrid.add_job("POINTWISE_GCI")
    prj_mgrid.add_job("FENSAP_RUN")

    prj_cgrid = base_project.clone()
    prj_cgrid.name("C Grid")
    prj_cgrid.set("PWS_REFINEMENT", 2)
    prj_cgrid.add_job("POINTWISE_GCI")
    prj_cgrid.add_job("FENSAP_RUN")

    # run the project


if __name__ == "__main__":
    main()
