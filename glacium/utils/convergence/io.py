from __future__ import annotations

from pathlib import Path
import re

__all__ = ["parse_headers", "read_history", "read_history_with_labels"]

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
