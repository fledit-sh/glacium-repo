"""Analyse a clean angle-of-attack sweep for the full power study.

The :func:`main` entry point reads all sweep runs, extracts aerodynamic
coefficients and generates plots plus a ``polar.csv`` file.

Key Functions
-------------
* :func:`load_runs` – collect AoA, CL and CD from each project.
* :func:`aoa_sweep_analysis` – generate plots and CSV data.
* :func:`main` – command line entry point.

Inputs
------
base_dir : Path | str, optional
    Base directory containing ``08_clean_sweep``.

Outputs
-------
Plots and ``polar.csv`` written to ``09_clean_sweep_results``.

Usage
-----
``python scripts/09_clean_sweep_analysis.py``

See Also
--------
``docs/full_power_study.rst`` for a complete workflow example.
"""

from __future__ import annotations

from pathlib import Path
import math
import matplotlib.pyplot as plt
import numpy as np

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log
from glacium.utils.convergence import project_cl_cd_stats

import scienceplots
plt.style.use(["science", "ieee"])

# Directory containing the baseline AoA=0 run
AOA0_DIR = Path("07_clean_aoa0")


def load_runs(root: Path, exclude_zero: bool = False) -> list[tuple[float, float, float, Project]]:
    """Return AoA, CL, CD and project for all runs under ``root``.

    Parameters
    ----------
    root:
        Directory containing the projects.
    exclude_zero:
        If ``True`` omit entries where ``AoA`` equals zero.
    """
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
        if exclude_zero and abs(aoa) < 1e-9:
            continue
        stats_dir = proj.root / "analysis" / "FENSAP"
        cl, cd = float("nan"), float("nan")
        # Prefer CL/CD from the FENSAP analysis stats if available
        cl_stats, _, cd_stats, _ = project_cl_cd_stats(stats_dir)
        if not (math.isnan(cl_stats) or math.isnan(cd_stats)):
            cl, cd = cl_stats, cd_stats
        else:
            try:
                cl = float(proj.get("LIFT_COEFFICIENT"))
                cd = float(proj.get("DRAG_COEFFICIENT"))
            except Exception:
                pass

        runs.append((aoa, cl, cd, proj))
    return runs


def first_drop_index(vals: list[float]) -> int:
    """Return index where values first decrease.

    The returned index can be used as an end slice to exclude data beyond
    the first drop in the sequence.  If no drop is detected the full length
    of ``vals`` is returned.
    """
    for i in range(1, len(vals)):
        if vals[i] < vals[i - 1]:
            return i
    return len(vals)


def aoa_sweep_analysis(runs: list[tuple[float, float, float, Project]], out_dir: Path) -> None:
    if not runs:
        log.error("No completed runs found.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    runs.sort(key=lambda t: t[0])

    aoa_vals = [r[0] for r in runs]
    cl_vals = [r[1] for r in runs]
    cd_vals = [r[2] for r in runs]

    cut = first_drop_index(cl_vals)

    data = np.column_stack((aoa_vals, cl_vals, cd_vals))
    np.savetxt(out_dir / "polar.csv", data,
               delimiter=",", header="AoA,CL,CD", comments="")

    # ---- CL vs AoA ----
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)   # größere Figure + höhere DPI
    ax.plot(aoa_vals[:cut], cl_vals[:cut], marker="+", linewidth=1.5)
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("CL")
    ax.grid(True, linestyle=':')
    ax.tick_params(axis='both', direction='in', length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "cl_vs_aoa.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # ---- CD vs AoA ----
    fig, ax = plt.subplots(figsize=(8, 5), dpi=600)
    ax.plot(aoa_vals[:cut], cd_vals[:cut], marker="+", linewidth=1.5)
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("CD")
    ax.grid(True, linestyle=':')
    ax.tick_params(axis='both', direction='in', length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "cd_vs_aoa.png", dpi=300, bbox_inches="tight")
    plt.close(fig)



def main(base_dir: Path | str = Path(""), aoa0_dir: Path | str | None = None) -> None:
    """Analyze a clean sweep located under ``base_dir``.

    Parameters
    ----------
    base_dir:
        Base directory containing the sweep projects.
    aoa0_dir:
        Optional override for the AoA=0 project directory.  Defaults to
        ``base_dir / AOA0_DIR``.
    """

    base = Path(base_dir)
    sweep_root = base / "08_clean_sweep"
    runs = load_runs(sweep_root, exclude_zero=True)

    # Insert the baseline AoA=0 coefficients from the dedicated project
    aoa0_root = Path(aoa0_dir) if aoa0_dir is not None else base / AOA0_DIR
    aoa0_runs = load_runs(aoa0_root)
    if aoa0_runs:
        aoa0 = aoa0_runs[0]
        runs.append((0.0, aoa0[1], aoa0[2], aoa0[3]))

    aoa_sweep_analysis(runs, base / "09_clean_sweep_results")


if __name__ == "__main__":
    main()
