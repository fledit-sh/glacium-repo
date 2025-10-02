"""Create and run multishot simulations for the full power study.

The script builds independent multishot projects that generate their own
meshes before executing runs with varying shot timing sequences.

Key Functions
-------------
* :func:`_run_project` – helper to instantiate and run a project.
* :func:`main` – command line entry point.

Inputs
------
base_dir : Path | str, optional
    Base directory where ``05_multishot`` will be created.
case_vars : dict[str, Any] | None, optional
    Case variable overrides. Provide ``PWS_REFINEMENT`` to change the default
    Pointwise mesh refinement level of 8. The value may also be hardcoded in
    this script if desired.

Outputs
-------
Projects under ``05_multishot`` with corresponding results.

Usage
-----
``python scripts/05_multishot_creation.py``

See Also
--------
``docs/full_power_study.rst`` for a complete workflow example.
"""

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
        "MESH_VISUALIZATION"
    ]
    for name in jobs:
        builder.add_job(name)

    proj = builder.create()

    proj.run()
    log.info(f"Completed multishot project {proj.uid} ({len(timings)} shots)")


def main(
    base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None
) -> None:
    """Create and run multishot projects generating new meshes."""

    base_path = Path(base_dir)
    base = Project(base_path / "05_multishot").name("multishot")
    # Default Pointwise refinement level. Can be overridden via ``case_vars`` or
    # by editing ``pws_ref`` directly in this script.
    pws_ref = 8
    if case_vars:
        pws_ref = case_vars.get("PWS_REFINEMENT", pws_ref)
        for key, val in case_vars.items():
            base.set(key, val)
    base.set("PWS_REFINEMENT", pws_ref)

    # Time dependency study
    def multishot(total_time, n_shots, initial=10):
        step = (total_time - initial) / n_shots
        return [initial] + [step] * n_shots
    #
    ref0 = [490, 1]
    # ref1 = multishot(490,1) + [1]
    # ref2 = multishot(490,2) + [1]
    # ref3 = multishot(490,4) + [1]
    # ref4 = multishot(490,8) + [1]
    # _run_project(base, ref0)
    # _run_project(base, ref1)
    # _run_project(base, ref2)
    # _run_project(base, ref3)
    # _run_project(base, ref4)
    #
    # ref5 = multishot(3222.5,25) + [1]
    # _run_project(base, ref5)

if __name__ == "__main__":
    main()
