from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log
from glacium.utils.convergence import project_cl_cd_stats
from glacium.post.analysis import momentum_coefficient

import scienceplots
plt.style.use(["science", "ieee"])

"""Analyze a clean angle-of-attack sweep.

Results are written to the ``aoa_sweep_results`` directory, including
``polar.csv`` and ``polar_momentum.csv``.
"""


def load_runs(root: Path) -> list[tuple[float, float, float, float, Project]]:
    """Return AoA, CL, CD, C_mu and project for all runs under ``root``."""
    pm = ProjectManager(root)
    runs: list[tuple[float, float, float, float, Project]] = []
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

        cmu = float("nan")
        cp_file = proj.root / "analysis" / "FENSAP" / "cp_curve.csv"
        if cp_file.exists():
            try:
                cp_df = pd.read_csv(cp_file)
                cmu = momentum_coefficient(cp_df)
            except Exception:
                pass

        runs.append((aoa, cl, cd, cmu, proj))
    return runs


def aoa_sweep_analysis(runs: list[tuple[float, float, float, float, Project]], out_dir: Path) -> None:
    if not runs:
        log.error("No completed runs found.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    runs.sort(key=lambda t: t[0])
    aoa_vals = [r[0] for r in runs]
    cl_vals = [r[1] for r in runs]
    cd_vals = [r[2] for r in runs]
    cmu_vals = [r[3] for r in runs]

    data = np.column_stack((aoa_vals, cl_vals, cd_vals))
    np.savetxt(out_dir / "polar.csv", data,
               delimiter=",", header="AoA,CL,CD", comments="")

    data_mom = np.column_stack((aoa_vals, cmu_vals))
    np.savetxt(out_dir / "polar_momentum.csv", data_mom,
               delimiter=",", header="AoA,C_mu", comments="")

    # ---- CL vs AoA ----
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)   # größere Figure + höhere DPI
    ax.plot(aoa_vals, cl_vals, marker="+", linewidth=1.5)
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("CL")
    ax.grid(True, linestyle=':')
    ax.tick_params(axis='both', direction='in', length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "cl_vs_aoa.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # ---- CD vs AoA ----
    fig, ax = plt.subplots(figsize=(8, 5), dpi=600)
    ax.plot(aoa_vals, cd_vals, marker="+", linewidth=1.5)
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("CD")
    ax.grid(True, linestyle=':')
    ax.tick_params(axis='both', direction='in', length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "cd_vs_aoa.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # ---- C_mu vs AoA ----
    fig, ax = plt.subplots(figsize=(8, 5), dpi=600)
    ax.plot(aoa_vals, cmu_vals, marker="+", linewidth=1.5)
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("C_mu")
    ax.grid(True, linestyle=":")
    ax.tick_params(axis="both", direction="in", length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "cmu_vs_aoa.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main(base_dir: Path | str = Path("")) -> None:
    """Analyze a clean sweep located under ``base_dir``."""

    base = Path(base_dir)
    root = base / "CleanSweep"
    runs = load_runs(root)
    aoa_sweep_analysis(runs, base / "aoa_sweep_results")


if __name__ == "__main__":
    main()
