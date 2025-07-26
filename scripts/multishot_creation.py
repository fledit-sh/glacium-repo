from __future__ import annotations

from pathlib import Path

from glacium.api import Project
from glacium.utils.logging import log

from full_power_gci import load_runs, gci_analysis2


def main(times: list[float] | None = None) -> None:
    """Create and run a multishot project using the best grid."""

    runs = load_runs(Path("GridDependencyStudy"))
    result = gci_analysis2(runs, Path("grid_dependency_results"))
    if result is None:
        return

    _, _, best_proj = result
    mesh_path = Project.get_mesh(best_proj)

    base = Project("Multishot").name("multishot")
    base.set("CASE_CHARACTERISTIC_LENGTH", best_proj.get("CASE_CHARACTERISTIC_LENGTH"))
    base.set("CASE_VELOCITY", best_proj.get("CASE_VELOCITY"))
    base.set("CASE_ALTITUDE", best_proj.get("CASE_ALTITUDE"))
    base.set("CASE_TEMPERATURE", best_proj.get("CASE_TEMPERATURE"))
    base.set("CASE_AOA", best_proj.get("CASE_AOA"))
    base.set("CASE_YPLUS", best_proj.get("CASE_YPLUS"))
    base.set("PWS_REFINEMENT", best_proj.get("PWS_REFINEMENT"))

    if times is None:
        times = [20.0, 40.0, 80.0]
    if len(times) != 3:
        raise ValueError("times must contain three values")

    shot_times = [10.0] + list(times)
    base.set("MULTISHOT_COUNT", len(shot_times))
    base.set("CASE_MULTISHOT", shot_times)

    jobs = [
        "MULTISHOT_RUN",
        "CONVERGENCE_STATS",
        "POSTPROCESS_MULTISHOT",
        "ANALYZE_MULTISHOT",
    ]
    for name in jobs:
        base.add_job(name)

    proj = base.create()
    Project.set_mesh(mesh_path, proj)
    proj.run()
    log.info(f"Completed multishot project {proj.uid}")


if __name__ == "__main__":
    main()
