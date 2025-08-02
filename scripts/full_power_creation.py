from pathlib import Path
from typing import Any

from glacium.api import Project
from glacium.utils.logging import log


def main(base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None) -> None:
    """Create and run grid refinement projects.

    Parameters
    ----------
    base_dir : Path | str, optional
        Directory in which the ``GridDependencyStudy`` folder will be created.
    case_vars : dict[str, Any] | None, optional
        Case variables overriding the defaults.
    """

    root = Path(base_dir) / "GridDependencyStudy"
    base = Project(root).name("grid")

    defaults: dict[str, Any] = {
        "CASE_CHARACTERISTIC_LENGTH": 0.431,
        "CASE_VELOCITY": 20,
        "CASE_ALTITUDE": 100,
        "CASE_TEMPERATURE": 263.15,
        "CASE_AOA": 0,
        "CASE_YPLUS": 0.3,
    }
    if case_vars:
        defaults.update(case_vars)

    for key, value in defaults.items():
        base.set(key, value)

    base_jobs = [
        "XFOIL_REFINE",
        "XFOIL_THICKEN_TE",
        "XFOIL_PW_CONVERT",
        "POINTWISE_GCI",
        "FLUENT2FENSAP",
        "FENSAP_RUN",
        "FENSAP_CONVERGENCE_STATS",
        "POSTPROCESS_SINGLE_FENSAP",
        "FENSAP_ANALYSIS",
    ]

    refinements = [0.125 * (2 ** i) for i in range(6,9)]
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
