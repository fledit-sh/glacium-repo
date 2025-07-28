from __future__ import annotations

from pathlib import Path

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


def main(base_dir: str | Path = ".") -> None:
    """Create and run several multishot projects using the best grid."""

    base_dir = Path(base_dir)

    runs = load_runs(base_dir / "GridDependencyStudy")
    result = gci_analysis2(runs, base_dir / "grid_dependency_results")
    if result is None:
        return

    _, _, best_proj = result
    mesh_path = Project.get_mesh(best_proj)

    base = Project(base_dir / "Multishot").name("multishot")
    base.set("CASE_CHARACTERISTIC_LENGTH", best_proj.get("CASE_CHARACTERISTIC_LENGTH"))
    base.set("CASE_VELOCITY", best_proj.get("CASE_VELOCITY"))
    base.set("CASE_ALTITUDE", best_proj.get("CASE_ALTITUDE"))
    base.set("CASE_TEMPERATURE", best_proj.get("CASE_TEMPERATURE"))
    base.set("CASE_AOA", best_proj.get("CASE_AOA"))
    base.set("CASE_YPLUS", best_proj.get("CASE_YPLUS"))
    base.set("PWS_REFINEMENT", best_proj.get("PWS_REFINEMENT"))

    for count in (1, 7, 16, 32):
        _run_project(base, mesh_path, count)


if __name__ == "__main__":
    main()
