from __future__ import annotations

from pathlib import Path
import re

from .io import parse_headers, read_history

__all__ = [
    "stats_last_n",
    "cl_cd_stats",
    "execution_time",
    "cl_cd_summary",
    "project_cl_cd_stats",
    "aggregate_report",
]


# Regex for extracting wall-clock time
_TIME_RE = re.compile(r"total simulation =\s*([0-9:.]+)")


def _parse_time(value: str) -> float:
    """Return seconds for ``HH:MM:SS`` strings."""

    h, m, s = value.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def stats_last_n(data: "np.ndarray", n: int = 15) -> tuple["np.ndarray", "np.ndarray"]:
    """Return column-wise mean and std of the last ``n`` rows in ``data``."""

    import numpy as np

    tail = data[-n:] if n else data
    return np.mean(tail, axis=0), np.std(tail, axis=0)


def cl_cd_stats(directory: Path, n: int = 15) -> "np.ndarray":
    """Return mean lift and drag coefficients from ``directory``."""

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
    """Return overall mean and std deviation of lift/drag coefficients."""

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
