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
    "cl_cd_stats",
    "aggregate_report",
    "plot_stats",
    "analysis",
    "analysis_file",
]

# Regex for header lines: ``# <index> <label>``
HEADER_RE = re.compile(r"^#\s*\d+\s+(.+)$")


def parse_headers(path: Path) -> list[str]:
    """Return column labels from the header section of ``path``.

    Leading and trailing whitespace in labels is stripped.
    """

    labels: list[str] = []
    for line in path.read_text().splitlines():
        if not line.lstrip().startswith("#"):
            break
        m = HEADER_RE.match(line)
        if m:
            labels.append(m.group(1).strip())
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


def cl_cd_stats(directory: Path, n: int = 15) -> "np.ndarray":
    """Return mean lift and drag coefficients from ``directory``.

    Parameters
    ----------
    directory:
        Location containing ``converg.fensap.*`` files.
    n:
        Number of trailing rows used when averaging.
    """

    import numpy as np

    root = Path(directory)
    results: list[tuple[int, float, float]] = []

    for file in sorted(root.glob("converg.fensap.*")):
        labels = parse_headers(file)
        try:
            cl_idx = labels.index("lift coefficient")
            cd_idx = labels.index("drag coefficient")
        except ValueError:
            continue

        data = read_history(file, n)
        tail = data[-n:] if n else data
        cl_mean = float(np.mean(tail[:, cl_idx]))
        cd_mean = float(np.mean(tail[:, cd_idx]))

        try:
            idx = int(file.name.split(".")[-1])
        except ValueError:
            idx = len(results)

        results.append((idx, cl_mean, cd_mean))

    return np.array(results, dtype=float)


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
    labels: "Iterable[str] | None" = None,
) -> None:
    """Write ``matplotlib`` plots visualising ``means`` and ``stds``."""

    import matplotlib.pyplot as plt
    import numpy as np

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

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

    first = next(iter(sorted(report_dir.glob("converg.fensap.*"))), None)
    labels = parse_headers(first) if first else []

    if means.size:
        plot_stats(idx, means, stds, out_dir, labels)

    clcd = cl_cd_stats(report_dir)
    if clcd.size:
        import numpy as np
        import matplotlib.pyplot as plt

        out_dir.mkdir(parents=True, exist_ok=True)

        np.savetxt(
            out_dir / "cl_cd_stats.csv",
            clcd,
            delimiter=",",
            header="index,CL,CD",
            comments="",
        )

        plt.figure()
        plt.plot(clcd[:, 0], clcd[:, 1], label="CL")
        plt.plot(clcd[:, 0], clcd[:, 2], label="CD")
        plt.xlabel("multishot index")
        plt.ylabel("coefficient")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(out_dir / "cl_cd.png")
        plt.close()


def analysis_file(cwd: Path, args: "Sequence[str | Path]") -> None:
    """Analyse a single FENSAP convergence file and generate plots.

    Parameters
    ----------
    cwd:
        Working directory supplied by :class:`~glacium.engines.py_engine.PyEngine`.
        Unused but kept for API compatibility.
    args:
        Sequence containing the input convergence file and the output directory.
    """

    if len(args) < 2:
        raise ValueError("analysis_file requires input file and output directory")

    file = Path(args[0])
    out_dir = Path(args[1])

    import numpy as np
    import matplotlib.pyplot as plt

    labels, data = read_history_with_labels(file)

    out_dir.mkdir(parents=True, exist_ok=True)

    iterations = np.arange(1, data.shape[0] + 1)
    for col in range(data.shape[1]):
        plt.figure()
        plt.plot(iterations, data[:, col], marker="o")
        plt.xlabel("iteration")
        ylabel = labels[col] if col < len(labels) else f"column {col}"
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(out_dir / f"column_{col:02d}.png")
        plt.close()

    mean, _ = stats_last_n(data, 15)
    variance = np.var(data[-15:], axis=0)

    with (out_dir / "stats.csv").open("w", newline="") as fh:
        fh.write("label,mean,variance\n")
        for col in range(data.shape[1]):
            label = labels[col] if col < len(labels) else f"column {col}"
            fh.write(f"{label},{mean[col]},{variance[col]}\n")

    try:
        cl_idx = labels.index("lift coefficient")
        cd_idx = labels.index("drag coefficient")
    except ValueError:
        return

    clcd = np.column_stack((iterations, data[:, cl_idx], data[:, cd_idx]))
    np.savetxt(
        out_dir / "cl_cd_stats.csv",
        clcd,
        delimiter=",",
        header="index,CL,CD",
        comments="",
    )

    plt.figure()
    plt.plot(iterations, data[:, cl_idx], label="CL")
    plt.plot(iterations, data[:, cd_idx], label="CD")
    plt.xlabel("iteration")
    plt.ylabel("coefficient")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "cl_cd.png")
    plt.close()
