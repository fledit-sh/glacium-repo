from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from glacium.api import Project
from glacium.utils.logging import log


def main(
    base_dir: str | Path = ".",
    case_vars: Mapping[str, Any] | None = None,
) -> None:
    """Create and run grid refinement projects."""

    base_dir = Path(base_dir)

    defaults: dict[str, Any] = {
        "CASE_CHARACTERISTIC_LENGTH": 0.431,
        "CASE_VELOCITY": 20,
        "CASE_ALTITUDE": 100,
        "CASE_TEMPERATURE": 263.15,
        "CASE_AOA": 0,
        "CASE_YPLUS": 0.3,
    }
    params = {**defaults, **(case_vars or {})}

    base = Project(base_dir / "GridDependencyStudy").name("grid")
    for key, value in params.items():
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
