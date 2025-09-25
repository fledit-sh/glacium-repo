"""
Compare clean and iced polar curves from the full power study — portrait edition.
Adds robust "power" plots with safe handling (positive-lift trimming, CD floor),
and places legends below plots in a sharp-cornered black box.

Outputs (under 12_polar_combined_results/):
  - aoa_cl_cd_twin_portrait.png
  - aoa_cl_over_cd_portrait.png
  - cd_cl_polar_portrait.png
  - aoa_M_portrait.png
  - aoa_dM_portrait.png
  - aoa_pct_change_portrait.png
  - Mclean_vs_Miced_scatter.png
  - aoa_eta_db_portrait.png  (optional bounded ratio in dB)
"""

from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence
import numpy as np
import matplotlib.pyplot as plt
import scienceplots

# -----------------------
# Global plotting config
# -----------------------
plt.style.use(["science", "ieee"])

USE_TEX = False  # set True if you want LaTeX (requires a working TeX install)
try:
    plt.rcParams.update({"text.usetex": bool(USE_TEX)})
except Exception:
    # Fallback gracefully if TeX is missing; mathtext still renders $...$
    plt.rcParams.update({"text.usetex": False})

FIGSIZE_PORTRAIT = (3.2, 4.2)   # width, height in inches (portrait)
DPI = 300

# -----------------------
# Legend helper
# -----------------------
def legend_below(ax, handles=None, labels=None, *, ncol=2, yoffset=-0.18,
                 facecolor="black", edgecolor="black", textcolor="white", framealpha=1.0):
    """
    Place a legend below the axes in a sharp-cornered black box.
    If handles/labels are provided, use them; otherwise use ax's artists.
    """
    if handles is None and labels is None:
        leg = ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, yoffset),
            ncol=ncol,
            frameon=True,
            fancybox=False,    # sharp corners
            framealpha=framealpha,
        )
    else:
        leg = ax.legend(
            handles=handles,
            labels=labels,
            loc="upper center",
            bbox_to_anchor=(0.5, yoffset),
            ncol=ncol,
            frameon=True,
            fancybox=False,
            framealpha=framealpha,
        )
    fr = leg.get_frame()
    fr.set_facecolor(facecolor)
    fr.set_edgecolor(edgecolor)
    fr.set_linewidth(0.8)
    for txt in leg.get_texts():
        txt.set_color(textcolor)
    # Make room so the legend isn't cut off
    ax.figure.subplots_adjust(bottom=0.28)
    return leg

# -----------------------
# Utilities
# -----------------------
def load_csv(csv_file: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return AoA, CL and CD arrays loaded from csv_file."""
    data = np.loadtxt(csv_file, delimiter=",", skiprows=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    aoa = data[:, 0]
    cl = data[:, 1]
    cd = data[:, 2]
    return aoa, cl, cd


def first_drop_index(vals: Sequence[float]) -> int:
    """Slice end index at the first decrease (includes the first down-step)."""
    for i in range(1, len(vals)):
        if vals[i] < vals[i - 1]:
            return i + 1
    return len(vals)


def trim_to_positive_cl(aoa, cl, cd, cl_min=0.0):
    """Trim leading region where CL <= cl_min; keep only positive-lift operation."""
    pos = np.flatnonzero(cl > cl_min)
    if pos.size == 0:
        # No positive-lift region
        z = slice(0, 0)
        return aoa[z], cl[z], cd[z]
    i0 = pos[0]
    return aoa[i0:], cl[i0:], cd[i0:]


def apply_cd_floor(aoa, cl, cd):
    """Remove points with non-physical or tiny CD to prevent blow-ups."""
    if cd.size == 0:
        return aoa, cl, cd
    cd_eps = max(1e-12, 1e-9 * np.nanmax(cd))
    mask = cd > cd_eps
    return aoa[mask], cl[mask], cd[mask]


def safe_power_metric(cl, cd):
    """M = CL^3 / CD^2 with NaN for non-positive CD."""
    cds = np.where(cd <= 0, np.nan, cd)
    return (cl ** 3) / (cds ** 2)


def interp_to_grid(x_src, y_src, x_grid):
    """1D linear interpolation with NaN outside range."""
    if x_src.size == 0 or y_src.size == 0 or x_grid.size == 0:
        return np.full_like(x_grid, np.nan, dtype=float)
    o = np.argsort(x_src)
    return np.interp(x_grid, x_src[o], y_src[o], left=np.nan, right=np.nan)


# -----------------------
# Classic combined plots
# -----------------------
def plot_combined(
    clean: tuple[np.ndarray, np.ndarray, np.ndarray],
    iced:  tuple[np.ndarray, np.ndarray, np.ndarray],
    out_dir: Path,
) -> None:
    """AoA–CL/CD twin, CL/CD vs AoA, and CD–CL polar."""
    aoa_clean, cl_clean, cd_clean = clean
    aoa_iced,  cl_iced,  cd_iced  = iced

    # Cut at first CL drop (as in your original)
    cut_clean = first_drop_index(cl_clean)
    cut_iced  = first_drop_index(cl_iced)
    aoa_clean, cl_clean, cd_clean = aoa_clean[:cut_clean], cl_clean[:cut_clean], cd_clean[:cut_clean]
    aoa_iced,  cl_iced,  cd_iced  = aoa_iced[:cut_iced],   cl_iced[:cut_iced],   cd_iced[:cut_iced]

    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Twin-y: AoA vs CL (left) and CD (right) ---
    fig, ax_cl = plt.subplots(figsize=FIGSIZE_PORTRAIT, dpi=DPI)
    ax_cd = ax_cl.twinx()
    ln1 = ax_cl.plot(aoa_clean, cl_clean, marker="^", markersize=5, linestyle="-", linewidth=0.9, label="CL clean")
    ln3 = ax_cd.plot(aoa_clean, cd_clean, marker="v", markersize=5, linestyle="--", linewidth=0.9, label="CD clean")
    ln2 = ax_cl.plot(aoa_iced,  cl_iced,  marker="^", markersize=5, linestyle="-", linewidth=0.9, label="CL iced")
    ln4 = ax_cd.plot(aoa_iced,  cd_iced,  marker="v", markersize=5, linestyle="--", linewidth=0.9, label="CD iced")

    ax_cl.set_xlabel("AoA (deg)")
    ax_cl.set_ylabel(r"$C_L$")
    ax_cd.set_ylabel(r"$C_D$")
    ax_cl.grid(True, linestyle=":")
    # Build a combined legend and place it below
    lines = ln1 + ln2 + ln3 + ln4
    labels = [l.get_label() for l in lines]
    legend_below(ax_cl, handles=lines, labels=labels, ncol=2, yoffset=-0.22)
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_cl_cd_twin_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --- (CL/CD) vs AoA ---
    def safe_ratio(cl, cd):
        cd_safe = np.where(cd <= 0, np.nan, cd)
        return cl / cd_safe

    ldr_clean = safe_ratio(cl_clean, cd_clean)
    ldr_iced  = safe_ratio(cl_iced,  cd_iced)

    fig, ax = plt.subplots(figsize=FIGSIZE_PORTRAIT, dpi=DPI)
    ax.plot(aoa_clean, ldr_clean, marker="^", linewidth=0.9, linestyle="-", label=r"$C_L/C_D$ clean")
    ax.plot(aoa_iced,  ldr_iced,  marker="v", linewidth=0.9, linestyle="-", label=r"$C_L/C_D$ iced")
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel(r"$C_L/C_D$")
    ax.grid(True, linestyle=":")
    legend_below(ax, ncol=2, yoffset=-0.22)
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_cl_over_cd_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --- CD vs CL polar (x=CD, y=CL) ---
    fig, ax = plt.subplots(figsize=FIGSIZE_PORTRAIT, dpi=DPI)
    ax.plot(cd_clean, cl_clean, marker="^", linewidth=0.9, linestyle="-", label="clean")
    ax.plot(cd_iced,  cl_iced,  marker="v", linewidth=0.9, linestyle="-", label="iced")
    ax.set_xlabel(r"$C_D$")
    ax.set_ylabel(r"$C_L$")
    ax.grid(True, linestyle=":")
    legend_below(ax, ncol=2, yoffset=-0.22)
    fig.tight_layout()
    fig.savefig(out_dir / "cd_cl_polar_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)


# -----------------------
# Power plots (robust)
# -----------------------
def add_power_plots(base_dir: Path | str = Path("")):
    """
    Robust power metric visualizations:
      M = C_L^3 / C_D^2
      - Trim to C_L > 0
      - Floor tiny C_D
      - Use ΔM and %ΔM (stable), optional η_dB
    """
    base_dir = Path(base_dir)
    out_dir = base_dir / "12_polar_combined_results"
    out_dir.mkdir(parents=True, exist_ok=True)

    clean_csv = base_dir / "09_clean_sweep_results" / "polar.csv"
    iced_csv  = base_dir / "11_iced_sweep_results" / "polar.csv"

    if not clean_csv.exists() or not iced_csv.exists():
        raise FileNotFoundError("Required polar.csv files not found.")

    # Load
    aoa_c, cl_c, cd_c = load_csv(clean_csv)
    aoa_i, cl_i, cd_i = load_csv(iced_csv)

    # Cut at first CL drop
    k_c = first_drop_index(cl_c)
    k_i = first_drop_index(cl_i)
    aoa_c, cl_c, cd_c = aoa_c[:k_c], cl_c[:k_c], cd_c[:k_c]
    aoa_i, cl_i, cd_i = aoa_i[:k_i], cl_i[:k_i], cd_i[:k_i]

    # Trim to positive lift region (ignore negative-lift operation)
    aoa_c, cl_c, cd_c = trim_to_positive_cl(aoa_c, cl_c, cd_c, cl_min=0.0)
    aoa_i, cl_i, cd_i = trim_to_positive_cl(aoa_i, cl_i, cd_i, cl_min=0.0)

    # Enforce tiny-CD floor (prevent singularities)
    aoa_c, cl_c, cd_c = apply_cd_floor(aoa_c, cl_c, cd_c)
    aoa_i, cl_i, cd_i = apply_cd_floor(aoa_i, cl_i, cd_i)

    # Compute M for each dataset
    M_c = safe_power_metric(cl_c, cd_c)
    M_i = safe_power_metric(cl_i, cd_i)

    # --------------- Plot: M vs AoA ---------------
    fig, ax = plt.subplots(figsize=(5, 8), dpi=DPI)
    ax.plot(aoa_c, M_c, marker="^", linestyle="-", linewidth=0.9, label=r"$M$ clean")
    ax.plot(aoa_i, M_i, marker="v", linestyle="-", linewidth=0.9, label=r"$M$ iced")
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel(r"$M = C_L^3 / C_D^2$")
    ax.grid(True, linestyle=":")
    legend_below(ax, ncol=2, yoffset=-0.16)
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_M_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # Build common AoA grid over overlap for comparative metrics
    if aoa_c.size and aoa_i.size:
        lo = max(np.nanmin(aoa_c), np.nanmin(aoa_i))
        hi = min(np.nanmax(aoa_c), np.nanmax(aoa_i))
        mask_grid = (aoa_c >= lo) & (aoa_c <= hi)
        aoa_grid = aoa_c[mask_grid]
    else:
        aoa_grid = np.array([], dtype=float)

    M_cg = interp_to_grid(aoa_c, M_c, aoa_grid)
    M_ig = interp_to_grid(aoa_i, M_i, aoa_grid)

    # Epsilon for relative operations (guard near-zero denominators)
    eps = max(1e-12, 1e-9 * (np.nanmax(M_c) if np.isfinite(np.nanmax(M_c)) else 1.0))
    ok  = np.isfinite(M_cg) & np.isfinite(M_ig)

    # --------------- Plot: ΔM = M_iced - M_clean ---------------
    dM = np.full_like(M_cg, np.nan)
    dM[ok] = M_ig[ok] - M_cg[ok]

    fig, ax = plt.subplots(figsize=(5, 8), dpi=DPI)
    ax.axhline(0, lw=0.8, ls=":")
    ax.plot(aoa_grid, dM, marker="o", lw=0.9, label=r"$\Delta M$")
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel(r"$\Delta M = M_{\mathrm{iced}} - M_{\mathrm{clean}}$")
    ax.grid(True, ls=":")
    legend_below(ax, ncol=1, yoffset=-0.14)
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_dM_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --------------- Plot: %ΔM (only where M_clean > eps) ---------------
    pct = np.full_like(M_cg, np.nan)
    ok_pct = ok & (M_cg > eps)
    pct[ok_pct] = (M_ig[ok_pct] - M_cg[ok_pct]) / M_cg[ok_pct] * 100.0

    fig, ax = plt.subplots(figsize=(5, 8), dpi=DPI)
    ax.axhline(0, lw=0.8, ls=":")
    ax.plot(aoa_grid, pct, marker="o", lw=0.9, label=r"$\%\ \Delta M$")
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel(r"$\%\ \Delta M$")
    ax.grid(True, ls=":")
    legend_below(ax, ncol=1, yoffset=-0.14)
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_pct_change_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --------------- Plot: M_clean vs M_iced (division-free sanity check) ---------------
    if M_c.size and np.isfinite(M_c).any() and np.isfinite(M_i).any():
        lo_line = np.nanmin([np.nanmin(M_c), np.nanmin(M_i)])
        hi_line = np.nanmax([np.nanmax(M_c), np.nanmax(M_i)])
        if not np.isfinite(lo_line) or not np.isfinite(hi_line) or lo_line == hi_line:
            lo_line, hi_line = 0.0, 1.0
    else:
        lo_line, hi_line = 0.0, 1.0

    fig, ax = plt.subplots(figsize=(5, 6.5), dpi=DPI)
    ax.plot([lo_line, hi_line], [lo_line, hi_line], lw=0.8, ls=":", label=r"$y=x$")
    ax.scatter(M_c, M_i, s=14, label="points")
    ax.set_xlabel(r"$M_{\mathrm{clean}}$")
    ax.set_ylabel(r"$M_{\mathrm{iced}}$")
    ax.grid(True, ls=":")
    legend_below(ax, ncol=2, yoffset=-0.12)
    fig.tight_layout()
    fig.savefig(out_dir / "Mclean_vs_Miced_scatter.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --------------- Optional: bounded ratio in dB ---------------
    eta_db = np.full_like(M_cg, np.nan)
    ok_db = ok & (M_cg > eps) & (M_ig > eps)
    eta_db[ok_db] = 10.0 * np.log10(M_ig[ok_db] / M_cg[ok_db])

    fig, ax = plt.subplots(figsize=(5, 8), dpi=DPI)
    ax.axhline(0, lw=0.8, ls=":")
    ax.plot(aoa_grid, eta_db, marker="o", lw=0.9, label=r"$10\log_{10}(M_{\mathrm{iced}}/M_{\mathrm{clean}})$")
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel(r"$10\log_{10}\!\left(\dfrac{M_{\mathrm{iced}}}{M_{\mathrm{clean}}}\right)\ \mathrm{dB}$")
    ax.grid(True, ls=":")
    legend_below(ax, ncol=1, yoffset=-0.14)
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_eta_db_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)


# -----------------------
# Main
# -----------------------
def main(base_dir: Path | str = Path("")) -> None:
    """Load sweep CSVs under base_dir and generate all plots."""
    base = Path(base_dir)
    clean_csv = base / "09_clean_sweep_results" / "polar.csv"
    iced_csv  = base / "11_iced_sweep_results" / "polar.csv"
    if not clean_csv.exists() or not iced_csv.exists():
        raise FileNotFoundError("polar.csv not found in sweep result directories")

    clean = load_csv(clean_csv)
    iced  = load_csv(iced_csv)

    out_dir = base / "12_polar_combined_results"
    plot_combined(clean, iced, out_dir)
    add_power_plots(base)


if __name__ == "__main__":
    main()
