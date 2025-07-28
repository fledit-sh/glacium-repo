from __future__ import annotations

from pathlib import Path

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


def plot_combined(
    clean: tuple[np.ndarray, np.ndarray, np.ndarray],
    iced: tuple[np.ndarray, np.ndarray, np.ndarray],
    out_dir: Path,
) -> None:
    """Plot combined clean and iced polar curves into ``out_dir``."""
    aoa_clean, cl_clean, cd_clean = clean
    aoa_iced, cl_iced, cd_iced = iced

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


def main() -> None:
    clean_csv = Path("aoa_sweep_results") / "polar.csv"
    iced_csv = Path("aoa_sweep_results_iced") / "polar.csv"
    clean = load_csv(clean_csv)
    iced = load_csv(iced_csv)
    plot_combined(clean, iced, Path("polar_combined_results"))


if __name__ == "__main__":
    main()
