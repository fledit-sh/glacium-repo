from __future__ import annotations

import os
from pathlib import Path


def get_runs_root() -> Path:
    """Return the directory used to store projects."""
    root = os.getenv("GLACIUM_RUNS_ROOT")
    if root:
        return Path(root)
    return Path("runs")

