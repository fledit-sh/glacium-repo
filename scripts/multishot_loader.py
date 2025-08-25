from __future__ import annotations

"""Utilities for selecting multishot projects.

This module exposes :func:`load_multishot_project` which locates the multishot
project under a given directory that contains the most shot entries.  It avoids
looking for solver output files and instead bases the selection purely on the
``CASE_MULTISHOT`` values stored in each project's configuration.
"""

from pathlib import Path
from typing import Iterable

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager

__all__ = ["load_multishot_project"]


def _shots_count(proj: Project) -> int:
    """Return the number of shot times configured for ``proj``.

    Projects may omit ``CASE_MULTISHOT`` or provide a non-iterable value; in
    those cases ``0`` is returned.
    """

    shots = proj.get("CASE_MULTISHOT", [])
    if isinstance(shots, Iterable):
        try:
            return len(list(shots))
        except TypeError:
            return 0
    return 0


def load_multishot_project(root: Path) -> Project:
    """Return the multishot project under ``root`` with most shot times.

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
