from __future__ import annotations

from pathlib import Path
from typing import Iterable

__all__ = ["plot_stats"]


def plot_stats(
    indices: Iterable[int],
    means: "np.ndarray",
    stds: "np.ndarray",
    out_dir: str | Path,
    labels: Iterable[str] | None = None,
) -> None:
    """Write ``matplotlib`` plots visualising ``means`` and ``stds``."""

    import matplotlib.pyplot as plt
    import numpy as np
    import scienceplots

    plt.style.use(["science", "ieee"])
    plt.rcParams["text.usetex"] = False

    out = Path(out_dir)
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    ind = np.array(list(indices))
    lbls = list(labels or [])
    for col in range(means.shape[1]):
        ylabel = lbls[col] if col < len(lbls) else f"column {col}"
        plt.figure()
        plt.errorbar(ind, means[:, col], yerr=stds[:, col], fmt="o-", capsize=3)
        plt.xlabel("multishot index")
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(fig_dir / f"column_{col:02d}.png")
        plt.close()
