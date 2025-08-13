from __future__ import annotations

from pathlib import Path
from typing import Any

from glacium.api import Project
from glacium.utils.logging import log


def _run_project(base: Project, timings: list[float]) -> None:
    """Instantiate ``base`` with the given ``timings`` and run it."""

    builder = base.clone()
    builder.set("CASE_MULTISHOT", timings)

    jobs = [
        "XFOIL_REFINE",
        "XFOIL_THICKEN_TE",
        "XFOIL_PW_CONVERT",
        "POINTWISE_GCI",
        "FLUENT2FENSAP",
        "MULTISHOT_RUN",
        "CONVERGENCE_STATS",
        "POSTPROCESS_MULTISHOT",
        "ANALYZE_MULTISHOT",
    ]
    for name in jobs:
        builder.add_job(name)

    proj = builder.create()

    proj.run()
    log.info(f"Completed multishot project {proj.uid} ({len(timings)} shots)")


def main(
    base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None
) -> None:
    """Create and run several multishot projects each generating a new grid."""

    base = Path(base_dir)

    base = Project(base / "03_multishot").name("multishot")

    if case_vars:
        for key, val in case_vars.items():
            base.set(key, val)

    # Time dependency study
    ref0 = [370]
    ref1 = [10, 360]
    ref2 = [10] + [120] * 3
    ref3 = [10] + [60] * 6

    _run_project(base, ref0)
    _run_project(base, ref1)
    _run_project(base, ref2)
    _run_project(base, ref3)


if __name__ == "__main__":
    main()
