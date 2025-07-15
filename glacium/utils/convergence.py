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
    "execution_time",
    "cl_cd_summary",
    "project_cl_cd_stats",
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


_TIME_RE = re.compile(r"total simulation =\s*([0-9:.]+)")


def _parse_time(value: str) -> float:
    """Return seconds for ``HH:MM:SS`` strings."""

    h, m, s = value.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def execution_time(file: Path) -> float:
    """Sum all ``total simulation`` times in ``file`` (seconds)."""

    total = 0.0
    for line in Path(file).read_text().splitlines():
        m = _TIME_RE.search(line)
        if m:
            total += _parse_time(m.group(1))
    return total


def cl_cd_summary(directory: Path, n: int = 15) -> tuple[float, float, float, float]:
    """Return mean and standard deviation for lift and drag coefficients."""

    data = cl_cd_stats(directory, n)
    if data.size:
        cl_mean = float(data[:, 1].mean())
        cl_std = float(data[:, 1].std())
        cd_mean = float(data[:, 2].mean())
        cd_std = float(data[:, 2].std())
        return cl_mean, cl_std, cd_mean, cd_std
    return float("nan"), float("nan"), float("nan"), float("nan")


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


def project_cl_cd_stats(report_dir: Path, n: int = 15) -> tuple[float, float, float, float]:
    """Return overall mean and std deviation of lift/drag coefficients.

    Parameters
    ----------
    report_dir:
        Directory containing ``converg.fensap.*`` files.
    n:
        Number of trailing rows considered when computing statistics.
    """

    import numpy as np

    first = next(iter(sorted(Path(report_dir).glob("converg.fensap.*"))), None)
    if first is None:
        return float("nan"), float("nan"), float("nan"), float("nan")

    labels = parse_headers(first)
    try:
        cl_idx = labels.index("lift coefficient")
        cd_idx = labels.index("drag coefficient")
    except ValueError:
        return float("nan"), float("nan"), float("nan"), float("nan")

    _, means, stds = aggregate_report(report_dir, n)
    if not means.size:
        return float("nan"), float("nan"), float("nan"), float("nan")

    cl_mean = float(np.mean(means[:, cl_idx]))
    cl_std = float(np.mean(stds[:, cl_idx]))
    cd_mean = float(np.mean(means[:, cd_idx]))
    cd_std = float(np.mean(stds[:, cd_idx]))

    return cl_mean, cl_std, cd_mean, cd_std


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
    fig_dir = out_dir / "figures"

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
        fig_dir.mkdir(parents=True, exist_ok=True)

        np.savetxt(
            out_dir / "cl_cd_stats.csv",
            clcd,
            delimiter=",",
            header="index,CL,CD",
            comments="",
        )

        # individual lift/drag plots
        plt.figure()
        plt.plot(clcd[:, 0], clcd[:, 1])
        plt.xlabel("multishot index")
        plt.ylabel("CL")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(fig_dir / "cl.png")
        plt.close()

        plt.figure()
        plt.plot(clcd[:, 0], clcd[:, 2])
        plt.xlabel("multishot index")
        plt.ylabel("CD")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(fig_dir / "cd.png")
        plt.close()

        # combined plot
        plt.figure()
        plt.plot(clcd[:, 0], clcd[:, 1], label="CL")
        plt.plot(clcd[:, 0], clcd[:, 2], label="CD")
        plt.xlabel("multishot index")
        plt.ylabel("coefficient")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / "cl_cd.png")
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
    fig_dir = out_dir / "figures"

    import numpy as np
    import matplotlib.pyplot as plt
    import csv

    labels, data = read_history_with_labels(file)

    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    iterations = np.arange(1, data.shape[0] + 1)
    for col in range(data.shape[1]):
        plt.figure()
        plt.plot(iterations, data[:, col], marker="o")
        plt.xlabel("iteration")
        ylabel = labels[col] if col < len(labels) else f"column {col}"
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(fig_dir / f"column_{col:02d}.png")
        plt.close()

    mean, _ = stats_last_n(data, 15)
    variance = np.var(data[-15:], axis=0)

    with (out_dir / "stats.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["label", "mean", "variance"])
        for col in range(data.shape[1]):
            label = labels[col] if col < len(labels) else f"column {col}"
            writer.writerow([label, mean[col], variance[col]])

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

    # individual lift/drag plots
    plt.figure()
    plt.plot(iterations, data[:, cl_idx])
    plt.xlabel("iteration")
    plt.ylabel("CL")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_dir / "cl.png")
    plt.close()

    plt.figure()
    plt.plot(iterations, data[:, cd_idx])
    plt.xlabel("iteration")
    plt.ylabel("CD")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_dir / "cd.png")
    plt.close()

    # combined plot
    plt.figure()
    plt.plot(iterations, data[:, cl_idx], label="CL")
    plt.plot(iterations, data[:, cd_idx], label="CD")
    plt.xlabel("iteration")
    plt.ylabel("coefficient")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "cl_cd.png")
    plt.close()
