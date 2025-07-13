"""Parsing helpers for solver timing information."""

from __future__ import annotations

from pathlib import Path
from collections import deque
import re

__all__ = ["parse_execution_time"]

# Pattern for lines like: "total simulation = 00:08:30.27"
_TOTAL_RE = re.compile(r"total simulation\s*=\s*([0-9:.]+)")
# Pattern for lines like: "Wall time for calculations:      508.852 s."
_WALL_RE = re.compile(r"Wall time for calculations:\s*([0-9.]+\s*s)\.?")


def parse_execution_time(path: Path, last_lines: int = 30) -> str | None:
    """Return the solver execution time from ``path``.

    Only the last ``last_lines`` of the file are scanned for known timing
    patterns.  If no pattern is found, ``None`` is returned.
    """

    lines = deque(maxlen=last_lines)
    with Path(path).open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            lines.append(line)

    tail = "".join(lines)
    for regex in (_TOTAL_RE, _WALL_RE):
        m = regex.search(tail)
        if m:
            return m.group(1).strip().rstrip(".")
    return None
