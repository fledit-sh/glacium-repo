"""Create and run a single-shot simulation for the full power study.

The :func:`main` entry point constructs a project with a freshly
generated grid and executes the DROP3D and ICE3D workflow.

Inputs
------
base_dir : Path | str, optional
    Base directory where ``03_single_shot`` will be created.
case_vars : dict[str, Any] | None, optional
    Case variable overrides passed to the project.

Outputs
-------
Simulation results in ``03_single_shot``.

Usage
-----
``python scripts/03_single_shot_creation.py``

See Also
--------
``docs/full_power_study.rst`` for a complete workflow example.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from glacium.api import Project
from glacium.utils.logging import log


def main(
    base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None
) -> None:
    """Create and run a single-shot DROP3D/ICE3D project generating a new grid."""

    base = Path(base_dir)
    builder = Project(base / "03_single_shot").name("single_shot")

    if case_vars:
        for key, val in case_vars.items():
            builder.set(key, val)
        if "CASE_MULTISHOT" in case_vars and "ICE_GUI_TOTAL_TIME" not in case_vars:
            builder.set("ICE_GUI_TOTAL_TIME", sum(case_vars["CASE_MULTISHOT"]))

    jobs = [
        "XFOIL_REFINE",
        "XFOIL_THICKEN_TE",
        "XFOIL_PW_CONVERT",
        "POINTWISE_GCI",
        "FLUENT2FENSAP",
        "FENSAP_RUN",
        "FENSAP_CONVERGENCE_STATS",
        "DROP3D_RUN",
        "DROP3D_CONVERGENCE_STATS",
        "ICE3D_RUN",
        "ICE3D_CONVERGENCE_STATS",
        "POSTPROCESS_SINGLE_FENSAP",
        "FENSAP_ANALYSIS",
    ]
    for j in jobs:
        builder.add_job(j)

    proj = builder.create()
    proj.run()
    log.info(f"Completed single-shot project {proj.uid}")


if __name__ == "__main__":
    main()
