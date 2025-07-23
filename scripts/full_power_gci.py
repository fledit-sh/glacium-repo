from __future__ import annotations

from pathlib import Path
import math
import matplotlib.pyplot as plt

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log
from glacium.utils.convergence import project_cl_cd_stats


def load_runs(root: Path) -> list[tuple[float, float, float, Project]]:
    """Return refinement factor, CL, CD and project for all runs."""
    pm = ProjectManager(root)
    runs: list[tuple[float, float, float, Project]] = []
    for uid in pm.list_uids():
        try:
            proj = Project.load(root, uid)
        except FileNotFoundError:
            continue
        try:
            factor = float(proj.get("PWS_REFINEMENT"))
        except Exception:
            continue
        cl, _, cd, _ = project_cl_cd_stats(proj.root / "analysis" / "FENSAP")
        runs.append((factor, cl, cd, proj))
    return runs


def gci_analysis(runs: list[tuple[float, float, float, Project]], out_dir: Path) -> None:
    """Compute GCI statistics and create summary plots."""
    if not runs:
        log.error("No completed runs found.")
        return

    runs.sort(key=lambda t: t[0])
    factors = [r[0] for r in runs]
    cl_vals = [r[1] for r in runs]
    cd_vals = [r[2] for r in runs]

    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure()
    plt.plot(factors, cl_vals, marker="o")
    plt.xlabel("PWS_REFINEMENT")
    plt.ylabel("CL")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_dir / "cl_vs_refinement.png")
    plt.close()

    plt.figure()
    plt.plot(factors, cd_vals, marker="o")
    plt.xlabel("PWS_REFINEMENT")
    plt.ylabel("CD")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_dir / "cd_vs_refinement.png")
    plt.close()

    if len(runs) < 3:
        log.error("At least three grids are required for GCI analysis.")
        return

    f1, phi1_cl, phi1_cd, _ = runs[0]
    f2, phi2_cl, phi2_cd, _ = runs[1]
    f3, phi3_cl, phi3_cd, _ = runs[2]
    r = f2 / f1

    p_cl = math.log(abs(phi3_cl - phi2_cl) / abs(phi2_cl - phi1_cl)) / math.log(r)
    p_cd = math.log(abs(phi3_cd - phi2_cd) / abs(phi2_cd - phi1_cd)) / math.log(r)

    Fs = 1.25
    gcis: list[tuple[float, Project]] = []
    for i in range(len(runs) - 1):
        phi_fine = runs[i][1]
        phi_coarse = runs[i + 1][1]
        gci = Fs * abs(phi_coarse - phi_fine) / (abs(phi_fine) * (r ** p_cl - 1)) * 100.0
        gcis.append((gci, runs[i][3]))

    best_gci, best_proj = min(gcis, key=lambda t: t[0])

    log.info(f"Order of accuracy (CL): {p_cl:.3f}")
    log.info(f"Order of accuracy (CD): {p_cd:.3f}")
    log.info(
        f"Lowest GCI: {best_gci:.3f}% for refinement {best_proj.get('PWS_REFINEMENT')}"
    )
    log.info(f"Recommended project: {best_proj.uid} ({best_proj.root})")


def main() -> None:
    root = Path("GridDependencyStudy")
    runs = load_runs(root)
    gci_analysis(runs, Path("grid_dependency_results"))


if __name__ == "__main__":
    main()
