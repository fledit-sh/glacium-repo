from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log
from glacium.utils.convergence import project_cl_cd_stats

import scienceplots
plt.style.use(["science", "ieee"])


def load_runs(root: Path) -> list[tuple[float, float, float, Project]]:
    """Return AoA, CL, CD and project for all runs under ``root``."""
    pm = ProjectManager(root)
    runs: list[tuple[float, float, float, Project]] = []
    for uid in pm.list_uids():
        try:
            proj = Project.load(root, uid)
        except FileNotFoundError:
            continue
        try:
            aoa = float(proj.get("CASE_AOA"))
        except Exception:
            continue

        try:
            cl = float(proj.get("LIFT_COEFFICIENT"))
            cd = float(proj.get("DRAG_COEFFICIENT"))
        except Exception:
            cl, _, cd, _ = project_cl_cd_stats(proj.root / "analysis" / "FENSAP")

        runs.append((aoa, cl, cd, proj))
    return runs


def aoa_sweep_analysis(runs: list[tuple[float, float, float, Project]], out_dir: Path) -> None:
    """Create CL/CD vs AoA plots from ``runs`` and save them in ``out_dir``."""
    if not runs:
        log.error("No completed runs found.")
        return

    runs.sort(key=lambda t: t[0])
    aoa_vals = [r[0] for r in runs]
    cl_vals = [r[1] for r in runs]
    cd_vals = [r[2] for r in runs]

    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure()
    plt.plot(aoa_vals, cl_vals, marker="+")
    plt.xlabel("AoA (deg)")
    plt.ylabel("CL")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_dir / "cl_vs_aoa.png")
    plt.close()

    plt.figure()
    plt.plot(aoa_vals, cd_vals, marker="+")
    plt.xlabel("AoA (deg)")
    plt.ylabel("CD")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_dir / "cd_vs_aoa.png")
    plt.close()


def main() -> None:
    root = Path("CleanSweep")
    runs = load_runs(root)
    aoa_sweep_analysis(runs, Path("aoa_sweep_results"))


if __name__ == "__main__":
    main()
