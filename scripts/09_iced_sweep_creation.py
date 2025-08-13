from __future__ import annotations

from pathlib import Path
from typing import Any

from glacium.api import Project
from glacium.utils.logging import log


def main(
    base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None
) -> None:
    """Generate and run iced angle-of-attack sweep projects."""

    base_path = Path(base_dir)

    base = Project(base_path / "09_iced_sweep").name("aoa_sweep")
    base.set("RECIPE", "fensap")
    base.set("PWS_REFINEMENT", 0.5)

    if case_vars:
        for key, val in case_vars.items():
            base.set(key, val)
        if "CASE_MULTISHOT" in case_vars and "ICE_GUI_TOTAL_TIME" not in case_vars:
            base.set("ICE_GUI_TOTAL_TIME", sum(case_vars["CASE_MULTISHOT"]))

    jobs = [
        "XFOIL_REFINE",
        "XFOIL_THICKEN_TE",
        "XFOIL_PW_CONVERT",
        "POINTWISE_GCI",
        "FLUENT2FENSAP",
        "DROP3D_RUN",
        "DROP3D_CONVERGENCE_STATS",
        "ICE3D_RUN",
        "ICE3D_CONVERGENCE_STATS",
        "FENSAP_CONVERGENCE_STATS",
        "POSTPROCESS_SINGLE_FENSAP",
        "FENSAP_ANALYSIS",
    ]

    for aoa in range(-4, 18, 2):
        builder = base.clone().set("CASE_AOA", aoa)
        for job in jobs:
            builder.add_job(job)
        proj = builder.create()
        proj.run()
        log.info(f"Completed angle {aoa}")


if __name__ == "__main__":
    main()
