from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from glacium.api import Project
from glacium.utils import reuse_mesh
from glacium.utils.logging import log

import importlib

multishot_analysis = importlib.import_module("06_multishot_analysis")
load_multishot_project = multishot_analysis.load_multishot_project


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
    """Create AOA sweep using the last iced grid from the multishot project."""

    base = Path(base_dir)

    ms_project = load_multishot_project(base / "05_multishot")
    grid_path = get_last_iced_grid(ms_project)

    base = Project(base / "09_iced_sweep").name("aoa_sweep")
    base.set("RECIPE", "fensap")

    params = {
        "CASE_CHARACTERISTIC_LENGTH": ms_project.get("CASE_CHARACTERISTIC_LENGTH"),
        "CASE_VELOCITY": ms_project.get("CASE_VELOCITY"),
        "CASE_ALTITUDE": ms_project.get("CASE_ALTITUDE"),
        "CASE_TEMPERATURE": ms_project.get("CASE_TEMPERATURE"),
        "CASE_YPLUS": ms_project.get("CASE_YPLUS"),
        "PWS_REFINEMENT": ms_project.get("PWS_REFINEMENT"),
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

    for aoa in range(-4, 18, 2):
        builder = base.clone().set("CASE_AOA", aoa)
        for job in jobs:
            builder.add_job(job)
        proj = builder.create()
        reuse_mesh(proj, grid_path, "FENSAP_RUN")
        proj.run()
        log.info(f"Completed angle {aoa}")


if __name__ == "__main__":
    main()
