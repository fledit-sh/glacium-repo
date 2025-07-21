from pathlib import Path

import glacium as glc
from glacium.api import Project


def main():
    # create projects below ./runs in the current directory

    run = (
        Project("Project01")
        .name("X Grid")

        # Case definition
        .set("CASE_ROUGHNESS", 0.0004)
        .set("CASE_CHARACTERISTIC_LENGTH", 0.431)
        .set("CASE_VELOCITY", 50)
        .set("CASE_ALTITUDE", 0)
        .set("CASE_TEMPERATURE", 263.15)
        .set("CASE_AOA", 0)
        .set("CASE_MVD", 20)
        .set("CASE_LWC", 0.0052)
        .set("CASE_YPLUS", 0.3)
        .set("PWS_REFINEMENT", 8)

        # Global settings
        .set("N_CPU", 12)
        .set("FSP_MAX_TIME_STEPS_PER_CYCLE", 700)
        .set("FSP_GUI_FENSAP_MAX_TIME_STEPS_PER_CYCLE", 700)

        # Job definitions
        .add_job("XFOIL_REFINE")
        .add_job("XFOIL_THICKEN_TE")
        .add_job("XFOIL_PW_CONVERT")
        .add_job("POINTWISE_GCI")
        .add_job("FLUENT2FENSAP")
        .add_job("FENSAP_RUN")
        .add_job("FENSAP_CONVERGENCE_STATS")

        .set("FSP_GUI_FENSAP_MAX_TIME_STEPS_PER_CYCLE", 120)
        .add_job("DROP3D_RUN")
        .add_job("DROP3D_CONVERGENCE_STATS")
        .add_job("ICE3D_RUN")
        .add_job("ICE3D_CONVERGENCE_STATS")
        .add_job("POSTPROCESS_SINGLE_FENSAP")
    )

    project_grid1 = run.create()

    # _ = run.clone()
    # _.name("F Grid")
    # _.set("PWS_REFINEMENT", 1)
    # project_grid2 = _.create()
    #
    # _ = run.clone()
    # _.name("M Grid")
    # _.set("PWS_REFINEMENT", 2)
    # project_grid3 = _.create()
    #
    # _ = run.clone()
    # _.name("C Grid")
    # _.set("PWS_REFINEMENT", 4)
    # project_grid4 = _.create()


    # project_grid1.run("XFOIL_REFINE")
    # project_grid1.run("XFOIL_THICKEN_TE")
    # project_grid1.run("XFOIL_PW_CONVERT")
    # project_grid1.run("POINTWISE_GCI")
    # project_grid1.run("FLUENT2FENSAP")
    #project_grid1.run("FENSAP_RUN")
    #project_grid1.run("FENSAP_CONVERGENCE_STATS")
    #project_grid1.run("DROP3D_RUN")
    #project_grid1.run("DROP3D_CONVERGENCE_STATS")
    #project_grid1.run("ICE3D_RUN")
    # project_grid1.run("ICE3D_CONVERGENCE_STATS")
    # project_grid1.run("POSTPROCESS_SINGLE_FENSAP")



if __name__ == "__main__":
    main()
