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


def default_case_file() -> Path:
    """Return the path to ``config/defaults/case.yaml``.

    Just like :func:`global_default_config`, the repository root is preferred
    over the installed package directory.
    """

    repo_root = Path(__file__).resolve().parents[2]
    pkg_root = Path(__file__).resolve().parents[1]

    a = repo_root / "config" / "defaults" / "case.yaml"
    b = pkg_root / "config" / "defaults" / "case.yaml"
    return a if a.exists() else b


def dejavu_font_file() -> Path:
    """Return the path to ``DejaVuSans.ttf`` used for PDF reports.

    The copy at the repository root is preferred over the installed package
    directory.
    """

    repo_root = Path(__file__).resolve().parents[2]
    pkg_root = Path(__file__).resolve().parents[1]

    a = repo_root / "glacium" / "DejaVuSans.ttf"
    b = pkg_root / "DejaVuSans.ttf"
    return a if a.exists() else b
