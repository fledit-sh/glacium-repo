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
plt.rcParams.update({"text.usetex": False})

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
    ln3 = ax_cd.plot(aoa_clean, cd_clean, color="darkgrey", marker="v", markersize=5,linewidth=0.8, linestyle="--", label="CD clean")

    # CD on right axis (use different linestyle to distinguish quantity)
    ln2 = ax_cl.plot(aoa_iced,  cl_iced, color="maroon", marker="^", markersize=5,linestyle="-", linewidth=0.8, label="CL iced")
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
    ax.plot(aoa_clean, ldr_clean, marker="^", linewidth=0.8, linestyle="-", label="(CL/CD) clean")
    ax.plot(aoa_iced,  ldr_iced,  marker="v", linewidth=0.8, linestyle="-", label="(CL/CD) iced")
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
    ax.plot(cd_clean, cl_clean, marker="^", linewidth=0.8, linestyle="-", label="clean")
    ax.plot(cd_iced,  cl_iced,  marker="v", linewidth=0.8, linestyle="-", label="iced")
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

# ---- BEGIN: Power plots extension ----
import numpy as _np
import matplotlib.pyplot as _plt

def _safe_power_metric(_cl, _cd):
    _cds = _np.where(_cd <= 0, _np.nan, _cd)
    return (_cl ** 3) / (_cds ** 2)

def _interp_to_grid(x_src, y_src, x_grid):
    o = _np.argsort(x_src)
    return _np.interp(x_grid, x_src[o], y_src[o], left=_np.nan, right=_np.nan)

def add_power_plots(base_dir=Path("")):
    base_dir = Path(base_dir)
    out_dir = base_dir / "12_polar_combined_results"
    out_dir.mkdir(parents=True, exist_ok=True)

    clean_csv = base_dir / "09_clean_sweep_results" / "polar.csv"
    iced_csv  = base_dir / "11_iced_sweep_results" / "polar.csv"

    # Robust load (AoA, CL, CD)
    def _load(csv_path):
        arr = _np.loadtxt(csv_path, delimiter=",", skiprows=1)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        return arr[:,0], arr[:,1], arr[:,2]

    aoa_c, cl_c, cd_c = _load(clean_csv)
    aoa_i, cl_i, cd_i = _load(iced_csv)

    # Optional: cut at first CL drop if present (mirror your polar logic)
    def _first_drop_index(vals):
        for k in range(1, len(vals)):
            if vals[k] < vals[k-1]:
                return k + 1
        return len(vals)

    cut_c = _first_drop_index(cl_c)
    cut_i = _first_drop_index(cl_i)

    aoa_c, cl_c, cd_c = aoa_c[:cut_c], cl_c[:cut_c], cd_c[:cut_c]
    aoa_i, cl_i, cd_i = aoa_i[:cut_i], cl_i[:cut_i], cd_i[:cut_i]

    # Compute M
    M_c = _safe_power_metric(cl_c, cd_c)
    M_i = _safe_power_metric(cl_i, cd_i)

    # Figure size: portrait; respect user's style by not overriding colors
    figsize = (5, 8)
    dpi = 300

    # --- M vs AoA (clean & iced) ---
    fig, ax = _plt.subplots(figsize=figsize, dpi=dpi)
    ax.plot(aoa_c, M_c, marker="^", linestyle="-", linewidth=0.8, label="M clean")
    ax.plot(aoa_i, M_i, marker="v", linestyle="-", linewidth=0.8, label="M iced")
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("M = CL^3 / CD^2")
    ax.grid(True, linestyle=":")
    ax.legend()
    ax.tick_params(axis="both", direction="in", length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_M_portrait.png", dpi=600, bbox_inches="tight")
    _plt.close(fig)

    # --- eta = M_iced / M_clean vs AoA (interpolate iced onto clean AoA where overlapping) ---
    lo = max(_np.nanmin(aoa_c), _np.nanmin(aoa_i))
    hi = min(_np.nanmax(aoa_c), _np.nanmax(aoa_i))
    mask_grid = (aoa_c >= lo) & (aoa_c <= hi)
    aoa_grid = aoa_c[mask_grid]

    M_c_grid = _interp_to_grid(aoa_c, M_c, aoa_grid)
    M_i_grid = _interp_to_grid(aoa_i, M_i, aoa_grid)
    eta = M_i_grid / M_c_grid

    fig, ax = _plt.subplots(figsize=figsize, dpi=dpi)
    ax.plot(aoa_grid, eta, marker="o", linestyle="-", linewidth=0.8, label="η = M_iced / M_clean")
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("η")
    ax.grid(True, linestyle=":")
    ax.legend()
    ax.tick_params(axis="both", direction="in", length=4)
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_eta_portrait.png", dpi=600, bbox_inches="tight")
    _plt.close(fig)

# Ensure the extension runs when the script is executed directly
if __name__ == "__main__":
    try:
        add_power_plots()
    except Exception as _e:
        print("[power-plots] skipped:", _e)
# ---- END: Power plots extension ----
