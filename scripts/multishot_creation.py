from __future__ import annotations

from pathlib import Path
from typing import Any

from glacium.api import Project
from glacium.utils.logging import log

from full_power_gci import load_runs, gci_analysis2


def _run_project(base: Project, mesh: Path, count: int) -> None:
    """Instantiate ``base`` with ``count`` shots and run it."""

    builder = base.clone()
    builder.set("MULTISHOT_COUNT", count)
    builder.set("CASE_MULTISHOT", [10.0])

    jobs = [
        "MULTISHOT_RUN",
        "CONVERGENCE_STATS",
        "POSTPROCESS_MULTISHOT",
        "ANALYZE_MULTISHOT",
    ]
    for name in jobs:
        builder.add_job(name)

    proj = builder.create()
    Project.set_mesh(mesh, proj)
    proj.run()
    log.info(f"Completed multishot project {proj.uid} ({count} shots)")


def main(
    base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None
) -> None:
    """Create and run several multishot projects using the best grid."""

    base = Path(base_dir)

    runs = load_runs(base / "GridDependencyStudy")
    result = gci_analysis2(runs, base / "grid_dependency_results")
    if result is None:
        return

    _, _, best_proj = result
    mesh_path = Project.get_mesh(best_proj)

    base = Project(base / "Multishot").name("multishot")

    params = {
        "CASE_CHARACTERISTIC_LENGTH": best_proj.get("CASE_CHARACTERISTIC_LENGTH"),
        "CASE_VELOCITY": best_proj.get("CASE_VELOCITY"),
        "CASE_ALTITUDE": best_proj.get("CASE_ALTITUDE"),
        "CASE_TEMPERATURE": best_proj.get("CASE_TEMPERATURE"),
        "CASE_AOA": best_proj.get("CASE_AOA"),
        "CASE_YPLUS": best_proj.get("CASE_YPLUS"),
        "PWS_REFINEMENT": best_proj.get("PWS_REFINEMENT"),
    }
    if case_vars:
        params.update(case_vars)

    for key, val in params.items():
        base.set(key, val)

    for count in (1, 7, 16, 32):
        _run_project(base, mesh_path, count)


if __name__ == "__main__":
    main()
