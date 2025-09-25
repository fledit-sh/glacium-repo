"""
Compare clean and iced polar curves — portrait edition with power metrics.

Plots:
- AoA vs CL (left) and CD (right) on twin y-axes
- CL/CD vs AoA
- CD vs CL polar
- Power metric M = CL^3 / CD^2 vs AoA (clean & iced)
- Relative efficiency η = M_iced / M_clean vs AoA
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import scienceplots

plt.style.use(["science", "ieee"])

FIGSIZE_PORTRAIT = (3, 4)
DPI = 300


def load_csv(csv_file: Path):
    data = np.loadtxt(csv_file, delimiter=",", skiprows=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return data[:, 0], data[:, 1], data[:, 2]


def first_drop_index(vals):
    for i in range(1, len(vals)):
        if vals[i] < vals[i - 1]:
            return i + 1
    return len(vals)


def safe_ratio(cl, cd):
    cd_safe = np.where(cd <= 0, np.nan, cd)
    return cl / cd_safe


def safe_power_metric(cl, cd):
    cd_safe = np.where(cd <= 0, np.nan, cd)
    return (cl ** 3) / (cd_safe ** 2)


def plot_combined(clean, iced, out_dir: Path):
    aoa_c, cl_c, cd_c = clean
    aoa_i, cl_i, cd_i = iced

    cut_c = first_drop_index(cl_c)
    cut_i = first_drop_index(cl_i)

    aoa_c, cl_c, cd_c = aoa_c[:cut_c], cl_c[:cut_c], cd_c[:cut_c]
    aoa_i, cl_i, cd_i = aoa_i[:cut_i], cl_i[:cut_i], cd_i[:cut_i]

    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Twin-y AoA vs CL & CD ---
    fig, ax_cl = plt.subplots(figsize=FIGSIZE_PORTRAIT, dpi=DPI)
    ax_cd = ax_cl.twinx()

    ax_cl.plot(aoa_c, cl_c, marker="+", linestyle="-", linewidth=0.8, label="CL clean")
    ax_cl.plot(aoa_i, cl_i, marker="+", linestyle="--", linewidth=0.8, label="CL iced")

    ax_cd.plot(aoa_c, cd_c, marker="x", linestyle="-", linewidth=0.8, label="CD clean")
    ax_cd.plot(aoa_i, cd_i, marker="x", linestyle="--", linewidth=0.8, label="CD iced")

    ax_cl.set_xlabel("AoA (deg)")
    ax_cl.set_ylabel("CL")
    ax_cd.set_ylabel("CD")

    lines = ax_cl.get_lines() + ax_cd.get_lines()
    labels = [l.get_label() for l in lines]
    ax_cl.legend(lines, labels, loc="best")

    ax_cl.grid(True, linestyle=":")
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_cl_cd_twin_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --- CL/CD vs AoA ---
    fig, ax = plt.subplots(figsize=FIGSIZE_PORTRAIT, dpi=DPI)
    ax.plot(aoa_c, safe_ratio(cl_c, cd_c), marker="+", linestyle="-", linewidth=0.8, label="(CL/CD) clean")
    ax.plot(aoa_i, safe_ratio(cl_i, cd_i), marker="+", linestyle="--", linewidth=0.8, label="(CL/CD) iced")
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("CL / CD")
    ax.grid(True, linestyle=":")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_cl_over_cd_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --- CD vs CL polar ---
    fig, ax = plt.subplots(figsize=FIGSIZE_PORTRAIT, dpi=DPI)
    ax.plot(cd_c, cl_c, marker="+", linestyle="-", linewidth=0.8, label="clean")
    ax.plot(cd_i, cl_i, marker="+", linestyle="--", linewidth=0.8, label="iced")
    ax.set_xlabel("CD")
    ax.set_ylabel("CL")
    ax.grid(True, linestyle=":")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "cd_cl_polar_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --- Power metric M = CL^3 / CD^2 ---
    M_c = safe_power_metric(cl_c, cd_c)
    M_i = safe_power_metric(cl_i, cd_i)

    fig, ax = plt.subplots(figsize=FIGSIZE_PORTRAIT, dpi=DPI)
    ax.plot(aoa_c, M_c, marker="^", linestyle="-", linewidth=0.8, label="M clean")
    ax.plot(aoa_i, M_i, marker="v", linestyle="-", linewidth=0.8, label="M iced")
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("M = CL^3 / CD^2")
    ax.grid(True, linestyle=":")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_M_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    # --- Relative efficiency η = M_iced / M_clean ---
    lo = max(np.nanmin(aoa_c), np.nanmin(aoa_i))
    hi = min(np.nanmax(aoa_c), np.nanmax(aoa_i))
    mask = (aoa_c >= lo) & (aoa_c <= hi)
    aoa_g = aoa_c[mask]

    def interp(x, y, xg):
        o = np.argsort(x)
        return np.interp(xg, x[o], y[o], left=np.nan, right=np.nan)

    M_cg = interp(aoa_c, M_c, aoa_g)
    M_ig = interp(aoa_i, M_i, aoa_g)
    eta = M_ig / M_cg

    fig, ax = plt.subplots(figsize=FIGSIZE_PORTRAIT, dpi=DPI)
    ax.plot(aoa_g, eta, marker="o", linestyle="-", linewidth=0.8, label="η = M_iced / M_clean")
    ax.set_xlabel("AoA (deg)")
    ax.set_ylabel("η")
    ax.grid(True, linestyle=":")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "aoa_eta_portrait.png", dpi=600, bbox_inches="tight")
    plt.close(fig)


def main(base_dir: Path | str = Path("")):
    base = Path(base_dir)
    clean_csv = base / "09_clean_sweep_results" / "polar.csv"
    iced_csv = base / "11_iced_sweep_results" / "polar.csv"

    clean = load_csv(clean_csv)
    iced = load_csv(iced_csv)

    plot_combined(clean, iced, base / "12_polar_combined_results")


if __name__ == "__main__":
    main()
