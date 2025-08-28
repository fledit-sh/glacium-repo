"""Create a clean angle-of-attack sweep for the full power study.

The :func:`main` entry point loads the most detailed multishot project,
reuses its mesh and executes FENSAP runs for a range of angles of attack.

Inputs
------
base_dir : Path | str, optional
    Base directory containing ``05_multishot``.
case_vars : dict[str, Any] | None, optional
    Case variable overrides passed to each project.

Outputs
-------
Projects created under ``07_clean_sweep``.

Usage
-----
``python scripts/07_clean_sweep_creation.py``

Requires a prior run of ``05_multishot_creation.py`` to supply the mesh.

See Also
--------
``docs/full_power_study.rst`` for a complete workflow example.
"""

from __future__ import annotations

from pathlib import Path

from glacium.api import Project
from glacium.utils import reuse_mesh, run_aoa_sweep
from glacium.utils.logging import log

from typing import Any

from multishot_loader import load_multishot_project


def main(
    base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None
) -> None:
    """Create AOA sweep projects using the grid from the multishot study.

    Parameters
    ----------
    base_dir : Path | str, optional
        Directory containing the ``05_multishot`` folder and where the
        ``07_clean_sweep`` project will be created.
    case_vars : dict[str, Any] | None, optional
        Case variables overriding those read from the selected grid.
    """

    base_path = Path(base_dir)

    try:
        ms_project = load_multishot_project(base_path / "05_multishot")
    except FileNotFoundError as err:
        log.error(str(err))
        return
    mesh_path = ms_project.get_mesh()

    base = Project(base_path / "08_clean_sweep").name("aoa_sweep")
    base.set("RECIPE", "fensap")

    params = {
        "CASE_CHARACTERISTIC_LENGTH": ms_project.get("CASE_CHARACTERISTIC_LENGTH"),
        "CASE_VELOCITY": ms_project.get("CASE_VELOCITY"),
        "CASE_ALTITUDE": ms_project.get("CASE_ALTITUDE"),
        "CASE_TEMPERATURE": ms_project.get("CASE_TEMPERATURE"),
        "CASE_YPLUS": ms_project.get("CASE_YPLUS"),
        "PWS_REFINEMENT": ms_project.get("PWS_REFINEMENT"),
    }
    if case_vars:
        params.update(case_vars)

    for key, val in params.items():
        base.set(key, val)

    jobs = ["FENSAP_CONVERGENCE_STATS", "FENSAP_ANALYSIS"]
    mesh = lambda proj: reuse_mesh(proj, mesh_path, "FENSAP_RUN")
    run_aoa_sweep(
        base,
        aoa_start=-4,
        aoa_end=16.0,
        step_sizes=[2.0, 1.0, 0.5],
        jobs=jobs,
        postprocess_aoas={},
        mesh_hook=mesh,
    )


if __name__ == "__main__":
    main()
