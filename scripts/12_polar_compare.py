"""Compare clean and iced polar curves from the full power study.

The :func:`main` entry point loads ``09_clean_sweep_results/polar.csv``
and ``11_iced_sweep_results/polar.csv`` then generates combined plots
under ``12_polar_combined_results`` for easy comparison.

Key Functions
-------------
* :func:`load_csv` – read AoA, CL and CD data from a CSV file.
* :func:`plot_combined` – render comparison plots.
* :func:`main` – command line entry point.

Inputs
------
base_dir : Path | str, optional
    Directory containing ``09_clean_sweep_results`` and
    ``11_iced_sweep_results``.

Outputs
-------
Plots in ``12_polar_combined_results``.

Usage
-----
``python scripts/12_polar_compare.py``

See Also
--------
``docs/full_power_study.rst`` for a complete workflow example.
"""

from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence
import matplotlib.pyplot as plt
import numpy as np
import scienceplots

plt.style.use(["science", "ieee"])


def load_csv(csv_file: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return AoA, CL and CD arrays loaded from ``csv_file``."""
    data = np.loadtxt(csv_file, delimiter=",", skiprows=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    aoa = data[:, 0]
    cl = data[:, 1]
    cd = data[:, 2]
    return aoa, cl, cd


def first_drop_index(vals: Sequence[float]) -> int:
    """Return slice end index at the first decrease.

    The returned value is intended for use as ``vals[:index]`` and therefore
    **includes** the first point after the peak where the sequence begins to
    decrease. If no drop is detected the full length of ``vals`` is returned.
    """

    for i in range(1, len(vals)):
        if vals[i] < vals[i - 1]:
            return i + 1
    return len(vals)


def plot_combined(
    clean: tuple[np.ndarray, np.ndarray, np.ndarray],
    iced: tuple[np.ndarray, np.ndarray, np.ndarray],
    out_dir: Path,
) -> None:
    """Plot combined clean and iced polar curves into ``out_dir``."""
    aoa_clean, cl_clean, cd_clean = clean
    aoa_iced, cl_iced, cd_iced = iced

    # Trim each dataset at the first CL drop
    cut_clean = first_drop_index(cl_clean)
    cut_iced = first_drop_index(cl_iced)
    aoa_clean, cl_clean, cd_clean = (
        aoa_clean[:cut_clean],
        cl_clean[:cut_clean],
        cd_clean[:cut_clean],
    )
    aoa_iced, cl_iced, cd_iced = (
        aoa_iced[:cut_iced],
        cl_iced[:cut_iced],
        cd_iced[:cut_iced],
    )

    out_dir.mkdir(parents=True, exist_ok=True)

    # --- CL vs AoA ---
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.plot(aoa_clean, cl_clean, marker="+", label="clean", linewidth=1.5)
    ax.plot(aoa_iced, cl_iced, marker="+", label="iced", linewidth=1.5)
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("CL")
    ax.grid(True, linestyle=":")
    ax.legend()
    ax.tick_params(axis="both", direction="in", length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "cl_combined.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --- CD vs AoA ---
    fig, ax = plt.subplots(figsize=(8, 5), dpi=600)
    ax.plot(aoa_clean, cd_clean, marker="+", label="clean", linewidth=1.5)
    ax.plot(aoa_iced, cd_iced, marker="+", label="iced", linewidth=1.5)
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("CD")
    ax.grid(True, linestyle=":")
    ax.legend()
    ax.tick_params(axis="both", direction="in", length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "cd_combined.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # --- CD vs CL ---
    fig, ax = plt.subplots(figsize=(8, 5), dpi=600)
    ax.plot(cd_clean, cl_clean, marker="+", label="clean", linewidth=1.5)
    ax.plot(cd_iced, cl_iced, marker="+", label="iced", linewidth=1.5)
    ax.set_xlabel("CL")
    ax.set_ylabel("CD")
    ax.grid(True, linestyle=":")
    ax.legend()
    ax.tick_params(axis="both", direction="in", length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "cd_cl_combined.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main(base_dir: Path | str = Path("")) -> None:
    """Load sweep CSVs under ``base_dir`` and plot comparisons.

    ``09_clean_sweep_results/polar.csv`` and
    ``11_iced_sweep_results/polar.csv`` are read relative to
    ``base_dir``.  Plots are written to ``12_polar_combined_results``.
    """

    base = Path(base_dir)
    clean_csv = base / "09_clean_sweep_results" / "polar.csv"
    iced_csv = base / "11_iced_sweep_results" / "polar.csv"
    if not clean_csv.exists() or not iced_csv.exists():
        raise FileNotFoundError("polar.csv not found in sweep result directories")

    clean = load_csv(clean_csv)
    iced = load_csv(iced_csv)
    plot_combined(clean, iced, base / "12_polar_combined_results")


if __name__ == "__main__":
    main()
