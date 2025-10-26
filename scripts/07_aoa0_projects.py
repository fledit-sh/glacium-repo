"""Run AoA=0 projects for clean and iced cases.

This script loads the most detailed multishot project, reuses its mesh to
run a clean FENSAP case at zero angle of attack and repeats the run using the
latest iced grid.  Both runs execute convergence statistics and analysis jobs.

Inputs
------
base_dir : Path | str, optional
    Base directory containing ``05_multishot``.
case_vars : dict[str, Any] | None, optional
    Case variable overrides.

Outputs
-------
Projects created under ``07_clean_aoa0`` and ``07_iced_aoa0``.

Usage
-----
``python scripts/07_aoa0_projects.py``
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import importlib.util

from glacium.api import Project
from glacium.utils import reuse_mesh
from glacium.utils.logging import log

from multishot_loader import load_multishot_project


# Jobs executed for each AoA=0 project.  Post-processing is appended so
# results from both clean and iced runs automatically include the
# generated figures and reports.
_JOBS = [
    "FENSAP_CONVERGENCE_STATS",
    "FENSAP_ANALYSIS",
    "POSTPROCESS_SINGLE_FENSAP",
]


def _load_iced_sweep_module():
    """Import and return the iced sweep script module."""
    script = Path(__file__).resolve().with_name("10_iced_sweep_creation.py")
    spec = importlib.util.spec_from_file_location("iced_sweep_creation", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _configure_builder(base: Project, params: dict[str, Any]) -> Project:
    base.set("RECIPE", "fensap")
    for key, val in params.items():
        base.set(key, val)
    return base


def _run_project(builder: Project, mesh_path: Path, roughness_path: Path | None = None) -> None:
    for job in _JOBS:
        builder.add_job(job)
    proj = builder.create()
    reuse_mesh(proj, mesh_path, "FENSAP_RUN", roughness=roughness_path)
    proj.run()


def main(
    base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None
) -> None:
    base_path = Path(base_dir)

    try:
        ms_project = load_multishot_project(base_path / "05_multishot")
    except FileNotFoundError as err:
        log.error(str(err))
        return

    params = {
        "CASE_CHARACTERISTIC_LENGTH": ms_project.get("CASE_CHARACTERISTIC_LENGTH"),
        "CASE_VELOCITY": ms_project.get("CASE_VELOCITY"),
        "CASE_ALTITUDE": ms_project.get("CASE_ALTITUDE"),
        # "CASE_TEMPERATURE": ms_project.get("CASE_TEMPERATURE"),
        "CASE_TEMPERATURE": 263.15,
        "CASE_YPLUS": ms_project.get("CASE_YPLUS"),
        "PWS_REFINEMENT": ms_project.get("PWS_REFINEMENT"),
    }
    if case_vars:
        params.update(case_vars)

    # Clean case
    clean_builder = _configure_builder(
        Project(base_path / "07_clean_aoa0").name("aoa0"), params
    )
    clean_builder.set("CASE_AOA", 0.0)
    _run_project(clean_builder, ms_project.get_mesh())

    # Iced case
    iced_module = _load_iced_sweep_module()
    grid_path, shot_index = iced_module.get_last_iced_grid(ms_project)  # type: ignore[attr-defined]
    roughness_path = grid_path.with_name(f"roughness.dat.ice.{shot_index}")
    if not roughness_path.exists():
        raise FileNotFoundError(
            f"Missing roughness file for shot {shot_index}: {roughness_path}"
        )
    iced_builder = _configure_builder(
        Project(base_path / "07_iced_aoa0").name("aoa0"), params
    )
    iced_builder.set("CASE_AOA", 0.0)
    _run_project(iced_builder, grid_path, roughness_path)


if __name__ == "__main__":
    main()
