"""Create an iced angle-of-attack sweep for the full power study.

This script copies the AoA=0 iced baseline project and extends it to a sweep
over a range of angles of attack.  The baseline run becomes the
0° entry in the sweep results.

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
import shutil
from typing import Any
import yaml
import re

from glacium.api import Project
from glacium.utils import reuse_mesh, run_aoa_sweep
from glacium.utils.logging import log
from glacium.managers.project_manager import ProjectManager


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

    sweep_root = base_path / "10_iced_sweep"
    dest_root = sweep_root / baseline_project.uid
    shutil.copytree(baseline_project.root, dest_root, dirs_exist_ok=True)

    cfg_file = dest_root / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text()) or {}
    cfg["BASE_DIR"] = str(dest_root)
    cfg_file.write_text(yaml.safe_dump(cfg, sort_keys=False))

    baseline_project = Project.load(sweep_root, baseline_project.uid)
    mesh_path = baseline_project.get_mesh()

    base = baseline_project.clone().name("aoa_sweep")
    base._jobs = []  # type: ignore[attr-defined]

    if case_vars:
        for key, val in case_vars.items():
            base.set(key, val)

    jobs = ["FENSAP_CONVERGENCE_STATS", "FENSAP_ANALYSIS"]
    mesh = lambda proj: reuse_mesh(proj, mesh_path, "FENSAP_RUN")
    run_aoa_sweep(
        base,
        aoa_start=-4.0,
        aoa_end=16.0,
        step_sizes=[2.0, 1.0, 0.5],
        jobs=jobs,
        postprocess_aoas={0.0},
        mesh_hook=mesh,
        skip_aoas={0.0},
        precomputed={0.0: baseline_project},
    )


if __name__ == "__main__":
    main()
