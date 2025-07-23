from glacium.api import Project
from glacium.utils.logging import log


def main() -> None:
    """Create and run grid refinement projects."""
    base = Project("GridDependencyStudy").name("X Grid")
    base.set("CASE_CHARACTERISTIC_LENGTH", 0.431)
    base.set("CASE_VELOCITY", 50)
    base.set("CASE_ALTITUDE", 0)
    base.set("CASE_TEMPERATURE", 263.15)
    base.set("CASE_AOA", 0)
    base.set("CASE_YPLUS", 0.3)

    base_jobs = [
        "XFOIL_REFINE",
        "XFOIL_THICKEN_TE",
        "XFOIL_PW_CONVERT",
        "POINTWISE_GCI",
        "FLUENT2FENSAP",
        "FENSAP_RUN",
        "FENSAP_CONVERGENCE_STATS",
        "FENSAP_ANALYSIS",
    ]

    refinements = [0.125 * (2 ** i) for i in range(8)]
    for factor in refinements:
        builder = base.clone()
        builder.set("PWS_REFINEMENT", factor)
        for job in base_jobs:
            builder.add_job(job)
        proj = builder.create()
        proj.run()
        log.info(
            f"Finished refinement {factor} for project {proj.uid} ({proj.root})"
        )


if __name__ == "__main__":
    main()
