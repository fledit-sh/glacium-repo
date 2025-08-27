"""Create an iced angle-of-attack sweep for the full power study.

This script extends the AoA=0 iced baseline project to an angle-of-attack
sweep.  The baseline run must be generated separately by
``07_aoa0_projects.py`` and is skipped here.

Inputs
------
base_dir : Path | str, optional
    Base directory containing ``07_iced_aoa0``.
case_vars : dict[str, Any] | None, optional
    Case variable overrides passed to each project.

Outputs
-------
Projects created under ``10_iced_sweep``.

Usage
-----
``python scripts/10_iced_sweep_creation.py``

Requires a prior run of ``07_aoa0_projects.py`` to supply the baseline.

See Also
--------
``docs/full_power_study.rst`` for a complete workflow example.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from glacium.api import Project
from glacium.utils import reuse_mesh, run_aoa_sweep
from glacium.utils.logging import log
from glacium.managers.project_manager import ProjectManager

from multishot_loader import load_multishot_project


def get_last_iced_grid(project: Project) -> Path:
    """Return the iced grid with the highest numeric suffix."""
    iced_dir = project.root / "run_MULTISHOT"
    pattern = re.compile(r"grid\.ice\.(\d{6})$")
    best: tuple[int, Path] | None = None
    for entry in iced_dir.iterdir():
        match = pattern.fullmatch(entry.name)
        if match:
            idx = int(match.group(1))
            if best is None or idx > best[0]:
                best = (idx, entry)
    if best is None:
        raise FileNotFoundError(f"No iced grid found in {iced_dir}")
    return best[1]


def main(
    base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None
) -> None:
    """Create AOA sweep projects using the AoA=0 iced baseline run."""

    base_path = Path(base_dir)
    src_root = base_path / "07_iced_aoa0"

    pm = ProjectManager(src_root)
    uids = pm.list_uids()
    if not uids:
        log.error(f"No projects found in {src_root}")
        return
    baseline_project = Project.load(src_root, uids[0])

    try:
        ms_project = load_multishot_project(base_path / "05_multishot")
    except FileNotFoundError as err:
        log.error(str(err))
        return
    iced_grid = get_last_iced_grid(ms_project)

    sweep_root = base_path / "10_iced_sweep"

    base = baseline_project.clone().name("aoa_sweep")
    base.runs_root = sweep_root
    base._params.pop("FSP_FILES_GRID", None)
    base._params.pop("ICE_GRID_FILE", None)
    base._params.pop("LIFT_COEFFICIENT", None)
    base._params.pop("DRAG_COEFFICIENT", None)
    base._jobs = []  # type: ignore[attr-defined]

    if case_vars:
        for key, val in case_vars.items():
            base.set(key, val)

    jobs = ["FENSAP_CONVERGENCE_STATS", "FENSAP_ANALYSIS"]
    mesh = lambda proj: reuse_mesh(proj, iced_grid, "FENSAP_RUN")
    run_aoa_sweep(
        base,
        aoa_start=-4.0,
        aoa_end=16.0,
        step_sizes=[2.0, 1.0, 0.5],
        jobs=jobs,
        postprocess_aoas=set(),
        mesh_hook=mesh,
        skip_aoas={0.0},
    )


if __name__ == "__main__":
    main()
