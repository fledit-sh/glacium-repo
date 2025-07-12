"""Helpers for analysing FENSAP convergence history files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import re

__all__ = [
    "parse_headers",
    "read_history",
    "read_history_with_labels",
    "stats_last_n",
    "aggregate_report",
    "plot_stats",
    "analysis",
]

# Regex for header lines: ``# <index> <label>``
HEADER_RE = re.compile(r"^#\s*\d+\s+(.+)$")


def parse_headers(path: Path) -> list[str]:
    """Return column labels from the header section of ``path``."""

    labels: list[str] = []
    for line in path.read_text().splitlines():
        if not line.lstrip().startswith("#"):
            break
        m = HEADER_RE.match(line)
        if m:
            labels.append(m.group(1))
    return labels


def read_history(file: str | Path, nrows: int | None = None) -> "np.ndarray":
    """Return the last ``nrows`` rows from ``file`` as ``numpy`` array.

    Header lines starting with ``#`` are ignored.
    """
    import numpy as np

    path = Path(file)
    data = [
        [float(val.replace("D", "E")) for val in line.split()]
        for line in path.read_text().splitlines()
        if not line.lstrip().startswith("#") and line.strip()
    ]
    arr = np.array(data, dtype=float)
    if nrows is not None:
        arr = arr[-nrows:]
    return arr


def read_history_with_labels(file: str | Path, nrows: int | None = None) -> tuple[list[str], "np.ndarray"]:
    """Return labels and data from ``file``.

    Parameters
    ----------
    file:
        Path to the convergence history file.
    nrows:
        If given, only the last ``nrows`` rows are returned.
    """
    import numpy as np

    path = Path(file)
    labels = parse_headers(path)
    data = [
        [float(val.replace("D", "E")) for val in line.split()]
        for line in path.read_text().splitlines()
        if not line.lstrip().startswith("#") and line.strip()
    ]
    arr = np.array(data, dtype=float)
    if nrows is not None:
        arr = arr[-nrows:]
    return labels, arr


def stats_last_n(data: "np.ndarray", n: int = 15) -> tuple["np.ndarray", "np.ndarray"]:
    """Return column-wise mean and std of the last ``n`` rows in ``data``."""

    import numpy as np

    tail = data[-n:] if n else data
    return np.mean(tail, axis=0), np.std(tail, axis=0)


def aggregate_report(
    directory: str | Path, n: int = 15
) -> tuple["np.ndarray", "np.ndarray", "np.ndarray"]:
    """Aggregate stats for all ``converg.fensap.*`` files in ``directory``."""

    import numpy as np

    root = Path(directory)
    means = []
    stds = []
    indices = []
    for file in sorted(root.glob("converg.fensap.*")):
        data = read_history(file, n)
        mean, std = stats_last_n(data, n)
        means.append(mean)
        stds.append(std)
        try:
            indices.append(int(file.name.split(".")[-1]))
        except ValueError:
            indices.append(len(indices))

    return (
        np.array(indices, dtype=int),
        np.vstack(means) if means else np.empty((0, 0)),
        np.vstack(stds) if stds else np.empty((0, 0)),
    )


def plot_stats(
    indices: "Iterable[int]",
    means: "np.ndarray",
    stds: "np.ndarray",
    out_dir: str | Path,
) -> None:
    """Write ``matplotlib`` plots visualising ``means`` and ``stds``."""

    import matplotlib.pyplot as plt
    import numpy as np

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    ind = np.array(list(indices))
    for col in range(means.shape[1]):
        plt.figure()
        plt.errorbar(ind, means[:, col], yerr=stds[:, col], fmt="o-", capsize=3)
        plt.xlabel("multishot index")
        plt.ylabel(f"column {col}")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(out / f"column_{col:02d}.png")
        plt.close()


def analysis(cwd: Path, args: "Sequence[str | Path]") -> None:
    """Aggregate convergence data and create plots.

    Parameters
    ----------
    cwd:
        Working directory supplied by :class:`~glacium.engines.py_engine.PyEngine`.
        Unused but kept for API compatibility.
    args:
        Sequence containing the input report directory and the output directory.
    """

    if len(args) < 2:
        raise ValueError("analysis requires input and output directory")

    report_dir = Path(args[0])
    out_dir = Path(args[1])

    idx, means, stds = aggregate_report(report_dir)
    if means.size:
        plot_stats(idx, means, stds, out_dir)
