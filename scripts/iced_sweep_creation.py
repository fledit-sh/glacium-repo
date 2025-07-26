from __future__ import annotations

from pathlib import Path
import re

from glacium.api import Project
from glacium.utils.logging import log

from multishot_analysis import load_multishot_project


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


def main() -> None:
    """Create AOA sweep using the last iced grid from the multishot project."""
    ms_project = load_multishot_project(Path("Multishot"))
    grid_path = get_last_iced_grid(ms_project)

    base = Project("IcedSweep").name("aoa_sweep")
    base.set("RECIPE", "fensap")
    base.set("CASE_CHARACTERISTIC_LENGTH", ms_project.get("CASE_CHARACTERISTIC_LENGTH"))
    base.set("CASE_VELOCITY", ms_project.get("CASE_VELOCITY"))
    base.set("CASE_ALTITUDE", ms_project.get("CASE_ALTITUDE"))
    base.set("CASE_TEMPERATURE", ms_project.get("CASE_TEMPERATURE"))
    base.set("CASE_YPLUS", ms_project.get("CASE_YPLUS"))
    base.set("PWS_REFINEMENT", ms_project.get("PWS_REFINEMENT"))
    base.set("PWS_REFINEMENT", 0.5)

    jobs = [
        "FENSAP_CONVERGENCE_STATS",
        "POSTPROCESS_SINGLE_FENSAP",
        "FENSAP_ANALYSIS",
    ]

    for aoa in range(-4, 21):
        builder = base.clone().set("CASE_AOA", aoa)
        for job in jobs:
            builder.add_job(job)
        proj = builder.create()
        Project.set_mesh(grid_path, proj)
        job = proj.job_manager._jobs.get("FENSAP_RUN")
        if job is not None:
            job.deps = ()
        proj.run()
        log.info(f"Completed angle {aoa}")


if __name__ == "__main__":
    main()
