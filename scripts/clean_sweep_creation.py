from __future__ import annotations

from pathlib import Path

from glacium.api import Project
from glacium.utils import reuse_mesh
from glacium.utils.logging import log

from full_power_gci import load_runs, gci_analysis2


from typing import Any


def main(
    base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None
) -> None:
    """Create AOA sweep projects using the best grid from the GCI study.

    Parameters
    ----------
    base_dir : Path | str, optional
        Directory containing the ``GridDependencyStudy`` folder and where the
        ``CleanSweep`` project will be created.
    case_vars : dict[str, Any] | None, optional
        Case variables overriding those read from the selected grid.
    """

    base_path = Path(base_dir)

    runs = load_runs(base_path / "GridDependencyStudy")
    result = gci_analysis2(runs, base_path / "grid_dependency_results")
    if result is None:
        return

    _, _, best_proj = result
    mesh_path = Project.get_mesh(best_proj)

    base = Project(base_path / "CleanSweep").name("aoa_sweep")
    base.set("RECIPE", "fensap")

    params = {
        "CASE_CHARACTERISTIC_LENGTH": best_proj.get("CASE_CHARACTERISTIC_LENGTH"),
        "CASE_VELOCITY": best_proj.get("CASE_VELOCITY"),
        "CASE_ALTITUDE": best_proj.get("CASE_ALTITUDE"),
        "CASE_TEMPERATURE": best_proj.get("CASE_TEMPERATURE"),
        "CASE_YPLUS": best_proj.get("CASE_YPLUS"),
        "PWS_REFINEMENT": best_proj.get("PWS_REFINEMENT"),
    }
    if case_vars:
        params.update(case_vars)

    for key, val in params.items():
        base.set(key, val)

    base.set("PWS_REFINEMENT", 0.5)

    jobs = [
        "FENSAP_CONVERGENCE_STATS",
        "POSTPROCESS_SINGLE_FENSAP",
        "FENSAP_ANALYSIS",
    ]

    for aoa in range(-4, 21, 8):
        builder = base.clone().set("CASE_AOA", aoa)
        for job in jobs:
            builder.add_job(job)
        proj = builder.create()
        reuse_mesh(proj, mesh_path, "FENSAP_RUN")
        proj.run()
        log.info(f"Completed angle {aoa}")


if __name__ == "__main__":
    main()
