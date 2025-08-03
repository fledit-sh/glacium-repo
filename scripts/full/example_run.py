from pathlib import Path

import glacium as glc
from glacium.api import Project


def main():
    # create projects below ./runs in the current directory

    prj = (
        Project("Project01")
        .name("X Grid")
        .create()
    )
    # Case definition
    prj.set("CASE_ROUGHNESS", 0.0004)
    prj.set("CASE_CHARACTERISTIC_LENGTH", 0.431)
    prj.set("CASE_VELOCITY", 50)
    prj.set("CASE_ALTITUDE", 0)
    prj.set("CASE_TEMPERATURE", 263.15)
    prj.set("CASE_AOA", 0)
    prj.set("CASE_MVD", 20)
    prj.set("CASE_LWC", 0.0052)
    prj.set("CASE_YPLUS", 0.3)
    prj.set("PWS_REFINEMENT", 8)

    # Global settings
    prj.set("N_CPU", 32)
    prj.set("FSP_MAX_TIME_STEPS_PER_CYCLE", 700)
    prj.set("FSP_GUI_FENSAP_MAX_TIME_STEPS_PER_CYCLE", 700)

    # Job definitions
    prj.add_job("XFOIL_REFINE")
    prj.add_job("XFOIL_THICKEN_TE")
    prj.add_job("XFOIL_PW_CONVERT")
    prj.add_job("POINTWISE_GCI")
    prj.add_job("FLUENT2FENSAP")
    prj.add_job("FENSAP_RUN")
    prj.add_job("FENSAP_CONVERGENCE_STATS")
    prj.add_job("POSTPROCESS_SINGLE_FENSAP")

    prj.set("CASE_MULTISHOT", [30] * 20)
    prj.set("ICE_GUI_TOTAL_TIME", 30)
    prj.add_job("MULTISHOT_RUN")
    prj.add_job("POSTPROCESS_MULTISHOT")
    prj.add_job("ANALYZE_MULTISHOT")


if __name__ == "__main__":
    main()
