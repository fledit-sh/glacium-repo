from __future__ import annotations

from pathlib import Path
from typing import Any

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log


def _run_project(base: Project, timings: list[float], mesh_path: Path) -> None:
    """Instantiate ``base`` with the given ``timings`` and run it."""

    builder = base.clone()
    builder.set("CASE_MULTISHOT", timings)

    jobs = [
        "MULTISHOT_RUN",
        "CONVERGENCE_STATS",
        "POSTPROCESS_MULTISHOT",
        "ANALYZE_MULTISHOT",
    ]
    for name in jobs:
        builder.add_job(name)

    proj = builder.create()

    # Reuse existing grid and clear dependencies
    proj.set_mesh(mesh_path)
    job = proj.job_manager._jobs.get("MULTISHOT_RUN")
    if job is not None:
        job.deps = ()

    proj.run()
    log.info(f"Completed multishot project {proj.uid} ({len(timings)} shots)")


def main(
    base_dir: Path | str = Path(""), case_vars: dict[str, Any] | None = None
) -> None:
    """Create and run multishot projects reusing the single-shot grid."""

    base = Path(base_dir)

    # Load mesh from the single-shot project
    single_root = base / "03_single_shot"
    pm = ProjectManager(single_root)
    uids = pm.list_uids()
    if not uids:
        log.error(f"No projects found in {single_root}")
        return
    if len(uids) > 1:
        log.warning("Multiple single-shot projects found, using the first one")
    single_proj = Project.load(single_root, uids[0])
    mesh_path = single_proj.get_mesh()

    base = Project(base / "05_multishot").name("multishot")

    if case_vars:
        for key, val in case_vars.items():
            base.set(key, val)

    # Time dependency study
    ref0 = [490]
    ref1 = [10, 480]
    ref2 = [10] + [240] * 2
    ref3 = [10] + [120] * 4
    ref4 = [10] + [60] * 8
    ref4 = [10] + [120] * 14
    _run_project(base, ref0, mesh_path)
    _run_project(base, ref1, mesh_path)
    _run_project(base, ref2, mesh_path)
    _run_project(base, ref3, mesh_path)
    _run_project(base, ref4, mesh_path)

if __name__ == "__main__":
    main()
