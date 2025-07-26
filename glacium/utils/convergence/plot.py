from __future__ import annotations

from pathlib import Path
from typing import Iterable
import numpy as np

__all__ = ["plot_stats"]


def plot_stats(
    indices: Iterable[int],
    means: np.ndarray,
    stds: np.ndarray,
    out_dir: str | Path,
    labels: Iterable[str] | None = None,
) -> None:
    """Write ``matplotlib`` plots visualising ``means`` and ``stds``."""

    import matplotlib.pyplot as plt
    import scienceplots  # noqa: F401
    from glacium.plotting import get_default_plotter

    plt.style.use(["science", "ieee"])
    plt.rcParams["text.usetex"] = False

    out = Path(out_dir)
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    ind = np.array(list(indices))
    lbls = list(labels or [])
    plotter = get_default_plotter()
    for col in range(means.shape[1]):
        ylabel = lbls[col] if col < len(lbls) else f"column {col}"
        fig, ax = plotter.new_figure()
        plotter.errorbar(ax, ind, means[:, col], stds[:, col], fmt="o-", capsize=3)
        ax.set_xlabel("multishot index")
        ax.set_ylabel(ylabel)
        ax.grid(True)
        fig.tight_layout()
        plotter.save(fig, fig_dir / f"column_{col:02d}.png")
        plotter.close(fig)
