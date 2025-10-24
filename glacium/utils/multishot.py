"""Helpers for working with multishot projects."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager

__all__ = ["load_multishot_project", "_shots_count"]


def _shots_count(proj: Project) -> int:
    """Return the number of configured shot times for ``proj``.

    The configuration key ``CASE_MULTISHOT`` may be absent or hold a non-iterable
    value.  In those situations ``0`` is returned.
    """

    try:
        shots = proj.get("CASE_MULTISHOT")
    except KeyError:
        shots = []
    if isinstance(shots, Iterable) and not isinstance(shots, (str, bytes)):
        try:
            return len(list(shots))
        except TypeError:
            return 0
    return 0


def load_multishot_project(root: Path) -> Project:
    """Return the multishot project under ``root`` with the largest shot count.

    Parameters
    ----------
    root:
        Directory containing multishot projects.

    Returns
    -------
    Project
        The project whose ``CASE_MULTISHOT`` list has the greatest length.

    Raises
    ------
    FileNotFoundError
        If no projects are present beneath ``root`` or none can be loaded.
    """

    pm = ProjectManager(root)
    uids = pm.list_uids()
    if not uids:
        raise FileNotFoundError(f"No projects found in {root}")

    best_proj: Project | None = None
    best_count = -1
    for uid in uids:
        try:
            proj = Project.load(root, uid)
        except FileNotFoundError:
            continue
        count = _shots_count(proj)
        if count > best_count:
            best_proj = proj
            best_count = count

    if best_proj is None:
        raise FileNotFoundError(f"No valid projects found in {root}")

    return best_proj
