from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log

import scienceplots

plt.style.use(["science", "ieee"])


def load_cp_curves(root: Path) -> list[tuple[float, pd.DataFrame]]:
    """Return AoA and Cp curve DataFrame for all runs under ``root``."""
    pm = ProjectManager(root)
    curves: list[tuple[float, pd.DataFrame]] = []
    for uid in pm.list_uids():
        try:
            proj = Project.load(root, uid)
        except FileNotFoundError:
            continue
        try:
            aoa = float(proj.get("CASE_AOA"))
        except Exception:
            continue
        cp_file = proj.root / "analysis" / "FENSAP" / "cp_curve.csv"
        if cp_file.exists():
            try:
                df = pd.read_csv(cp_file)
            except Exception:
                continue
            curves.append((aoa, df))
    curves.sort(key=lambda t: t[0])
    return curves


def animate_cp_curves(curves: list[tuple[float, pd.DataFrame]], outfile: Path, fps: int = 2) -> None:
    if not curves:
        log.error("No Cp curves found.")
        return

    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
    ax.set_xlabel(r"$x/c$")
    ax.set_ylabel(r"$C_p$")
    ax.grid(True, ls=":", lw=0.5)
    ax.invert_yaxis()

    line, = ax.plot([], [], "-k", lw=1.0)
    title = ax.text(0.05, 0.95, "", transform=ax.transAxes, ha="left", va="top")

    def init() -> list[plt.Artist]:
        line.set_data([], [])
        title.set_text("")
        return [line, title]

    def update(frame: int) -> list[plt.Artist]:
        aoa, df = curves[frame]
        line.set_data(df["x_c"], df["Cp"])
        title.set_text(f"AoA = {aoa:g}°")
        return [line, title]

    ani = FuncAnimation(fig, update, frames=len(curves), init_func=init, blit=True)
    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    ani.save(outfile, writer=PillowWriter(fps=fps))
    plt.close(fig)


def main() -> None:
    curves = load_cp_curves(Path("CleanSweep"))
    animate_cp_curves(curves, Path("aoa_sweep_results") / "cp_curves.gif")


if __name__ == "__main__":
    main()
