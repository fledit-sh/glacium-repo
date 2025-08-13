from __future__ import annotations

from pathlib import Path

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log


from typing import Any


def main(
    base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None
) -> None:
    """Create AOA sweep projects using the grid from the single-shot study.

    Parameters
    ----------
    base_dir : Path | str, optional
        Directory containing the ``01_grid_dependency_study`` folder and where the
        ``07_clean_sweep`` project will be created.
    case_vars : dict[str, Any] | None, optional
        Case variables overriding those read from the selected grid.
    """

    base_path = Path(base_dir)

    single_root = base_path / "05_single_shot"
    pm = ProjectManager(single_root)
    uids = pm.list_uids()
    if not uids:
        log.error(f"No projects found in {single_root}")
        return
    if len(uids) > 1:
        log.warning("Multiple single-shot projects found, using the first one")
    single_proj = Project.load(single_root, uids[0])
    mesh_path = single_proj.get_mesh()

    base = Project(base_path / "07_clean_sweep").name("aoa_sweep")
    base.set("RECIPE", "fensap")

    params = {
        "CASE_CHARACTERISTIC_LENGTH": single_proj.get("CASE_CHARACTERISTIC_LENGTH"),
        "CASE_VELOCITY": single_proj.get("CASE_VELOCITY"),
        "CASE_ALTITUDE": single_proj.get("CASE_ALTITUDE"),
        "CASE_TEMPERATURE": single_proj.get("CASE_TEMPERATURE"),
        "CASE_YPLUS": single_proj.get("CASE_YPLUS"),
        "PWS_REFINEMENT": single_proj.get("PWS_REFINEMENT"),
    }
    if case_vars:
        params.update(case_vars)

    for key, val in params.items():
        base.set(key, val)

    #base.set("PWS_REFINEMENT", 0.5)

    jobs = [
        "FENSAP_CONVERGENCE_STATS",
        "POSTPROCESS_SINGLE_FENSAP",
        "FENSAP_ANALYSIS",
    ]

    for aoa in range(-4, 18, 2):
        builder = base.clone().set("CASE_AOA", aoa)
        for job in jobs:
            builder.add_job(job)
        proj = builder.create()
        proj.set_mesh(mesh_path)
        job = proj.job_manager._jobs.get("FENSAP_RUN")
        if job is not None:
            job.deps = ()
        proj.run()
        log.info(f"Completed angle {aoa}")


if __name__ == "__main__":
    main()
