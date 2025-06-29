from __future__ import annotations

from pathlib import Path


def global_default_config() -> Path:
    """Return the path to ``config/defaults/global_default.yaml``.

    The function first looks for ``config/defaults`` at the repository root
    and falls back to the package directory. This mirrors the behaviour
    previously duplicated across multiple modules.
    """

    repo_root = Path(__file__).resolve().parents[2]
    pkg_root = Path(__file__).resolve().parents[1]

    a = repo_root / "config" / "defaults" / "global_default.yaml"
    b = pkg_root / "config" / "defaults" / "global_default.yaml"
    return a if a.exists() else b
