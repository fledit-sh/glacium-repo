from pathlib import Path

from glacium.api import Run

def main():
    # create projects below ./runs in the current directory
    run = (
        Run("Project01")
        .name("X Grid")

        # Case definition
        .set("CASE_ROUGHNESS", 50)
        .set("CASE_CHARACTERISTIC_LENGTH", 0.431)
        .set("CASE_VELOCITY", 50)
        .set("CASE_ALTITUDE", 0)
        .set("CASE_TEMPERATURE", 263.15)
        .set("CASE_AOA", 0)
        .set("CASE_MVD", 20)
        .set("CASE_LWC", 0.0052)
        .set("CASE_YPLUS", 0.3)
        .set("PWS_REFINEMENT", 0.5)

        .add_job("XFOIL_REFINE")
        .add_job("XFOIL_THICKEN_TE")
        .add_job("XFOIL_PW_CONVERT")
        .add_job("POINTWISE_GCI")
        .add_job("FLUENT2FENSAP")
        .add_job("FENSAP_RUN")
        .add_job("FENSAP_CONVERGENCE_STATS")
    )

    project_grid1 = run.create()

    _ = run.clone()
    _.name("F Grid")
    _.set("PWS_REFINEMENT", 1)
    project_grid2 = _.create()

    _ = run.clone()
    _.name("M Grid")
    _.set("PWS_REFINEMENT", 2)
    project_grid3 = _.create()

    _ = run.clone()
    _.name("C Grid")
    _.set("PWS_REFINEMENT", 4)
    project_grid4 = _.create()

    project_grid1.run()
    project_grid2.run()
    project_grid3.run()
    project_grid4.run()


if __name__ == "__main__":
    main()
