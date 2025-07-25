from pathlib import Path

from glacium.api import Project
from glacium.utils.logging import log

from full_power_gci import load_runs, gci_analysis2


def main() -> None:
    """Create AOA sweep projects using the best grid from the GCI study."""

    runs = load_runs(Path("GridDependencyStudy"))
    result = gci_analysis2(runs, Path("grid_dependency_results"))
    if result is None:
        return

    _, _, best_proj = result
    mesh_path = Project.get_mesh(best_proj)

    base = Project("CleanSweep").name("aoa_sweep")
    base.set("CASE_CHARACTERISTIC_LENGTH", best_proj.get("CASE_CHARACTERISTIC_LENGTH"))
    base.set("CASE_VELOCITY", best_proj.get("CASE_VELOCITY"))
    base.set("CASE_ALTITUDE", best_proj.get("CASE_ALTITUDE"))
    base.set("CASE_TEMPERATURE", best_proj.get("CASE_TEMPERATURE"))
    base.set("CASE_YPLUS", best_proj.get("CASE_YPLUS"))
    base.set("PWS_REFINEMENT", best_proj.get("PWS_REFINEMENT"))
    base.set("PWS_REFINEMENT", 0.5)

    jobs = [
        "FENSAP_RUN",
        "FENSAP_CONVERGENCE_STATS",
        "POSTPROCESS_SINGLE_FENSAP",
        "FENSAP_ANALYSIS",
    ]

    for aoa in range(-4, 20):
        builder = base.clone().set("CASE_AOA", aoa)
        for job in jobs:
            builder.add_job(job)
        proj = builder.create()
        Project.set_mesh(mesh_path, proj)
        proj.run()
        log.info(f"Completed angle {aoa}")


if __name__ == "__main__":
    main()
