"""
Compare clean and iced polar curves from the full power study — portrait edition.

Changes vs. original:
- Portrait ("hochkant") figures for better paper layout.
- Single AoA plot with two y-axes: left=CL, right=CD.
- New efficiency plot: CL/CD vs AoA.
- Fixed labels for the CD–CL polar (x=CD, y=CL).
"""

from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence
import matplotlib.pyplot as plt
import numpy as np
import scienceplots

# Use the same scientific style as the original script
plt.style.use(["science", "ieee"])

FIGSIZE_PORTRAIT = (3, 4)   # width, height in inches (hochkant)
DPI = 300


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
    """Plot combined clean and iced polar curves into ``out_dir`` (portrait)."""
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

    # --- Twin‑y portrait: AoA vs CL (left) and CD (right) ---
    fig, ax_cl = plt.subplots(figsize=FIGSIZE_PORTRAIT, dpi=DPI)
    ax_cd = ax_cl.twinx()

    # CL on left axis
    ln1 = ax_cl.plot(aoa_clean, cl_clean, color="dimgray", marker="^", markersize=5, linestyle="-", linewidth=0.8, label="CL clean")
    ln2 = ax_cl.plot(aoa_iced,  cl_iced, color="grey", marker="^", markersize=5,linestyle="-", linewidth=0.8, label="CL iced")

    # CD on right axis (use different linestyle to distinguish quantity)
    ln3 = ax_cd.plot(aoa_clean, cd_clean, color="darkgrey", marker="v", markersize=5,linewidth=0.8, linestyle="--", label="CD clean")
    ln4 = ax_cd.plot(aoa_iced,  cd_iced,  color="firebrick", marker="v", markersize=5,linewidth=0.8, linestyle="--", label="CD iced")

    ax_cl.set_xlabel("AoA (deg)")
    ax_cl.set_ylabel("CL")
    ax_cd.set_ylabel("CD")

    ax_cl.grid(True, linestyle=":")
    ax_cl.tick_params(axis="both", direction="in", length=4)
    ax_cd.tick_params(axis="both", direction="in", length=4)

    # Build a combined legend
    lines = ln1 + ln2 + ln3 + ln4
    labels = [l.get_label() for l in lines]
    ax_cl.legend(lines, labels, loc="best", frameon=True)

    fig.tight_layout()
    fig.savefig(out_dir / "aoa_cl_cd_twin_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --- CL/CD (efficiency) vs AoA — portrait ---
    # Guard against division by zero / negative drag
    def safe_ratio(cl, cd):
        cd_safe = np.where(cd <= 0, np.nan, cd)
        return cl / cd_safe

    ldr_clean = safe_ratio(cl_clean, cd_clean)
    ldr_iced  = safe_ratio(cl_iced,  cd_iced)

    fig, ax = plt.subplots(figsize=FIGSIZE_PORTRAIT, dpi=DPI)
    ax.plot(aoa_clean, ldr_clean, marker="+", linewidth=0.8, linestyle="-", label="(CL/CD) clean")
    ax.plot(aoa_iced,  ldr_iced,  marker="+", linewidth=0.8, linestyle="-", label="(CL/CD) iced")
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("CL / CD")
    ax.grid(True, linestyle=":")
    ax.legend()
    ax.tick_params(axis="both", direction="in", length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_cl_over_cd_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --- CD vs CL polar — portrait (label fix) ---
    fig, ax = plt.subplots(figsize=FIGSIZE_PORTRAIT, dpi=DPI)
    ax.plot(cd_clean, cl_clean, marker="+", linewidth=0.8, linestyle="-", label="clean")
    ax.plot(cd_iced,  cl_iced,  marker="+", linewidth=0.8, linestyle="-", label="iced")
    ax.set_xlabel("CD")  # x = CD
    ax.set_ylabel("CL")  # y = CL
    ax.grid(True, linestyle=":")
    ax.legend()
    ax.tick_params(axis="both", direction="in", length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "cd_cl_polar_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)


def main(base_dir: Path | str = Path("")) -> None:
    """Load sweep CSVs under ``base_dir`` and plot comparisons (portrait).

    Reads:
      * ``09_clean_sweep_results/polar.csv``
      * ``11_iced_sweep_results/polar.csv``

    Writes:
      * ``12_polar_combined_results/aoa_cl_cd_twin_portrait.png``
      * ``12_polar_combined_results/aoa_cl_over_cd_portrait.png``
      * ``12_polar_combined_results/cd_cl_polar_portrait.png``
    """
    base = Path(base_dir)
    clean_csv = base / "09_clean_sweep_results" / "polar.csv"
    iced_csv  = base / "11_iced_sweep_results" / "polar.csv"
    if not clean_csv.exists() or not iced_csv.exists():
        raise FileNotFoundError("polar.csv not found in sweep result directories")

    clean = load_csv(clean_csv)
    iced  = load_csv(iced_csv)
    plot_combined(clean, iced, base / "12_polar_combined_results")


if __name__ == "__main__":
    main()
