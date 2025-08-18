from __future__ import annotations

"""Simple helpers to analyse multishot projects.

The module exposes :func:`load_multishot_project` to locate the multishot
project with the highest number of shots based on ``CASE_MULTISHOT`` and a
small :func:`main` entry point mirroring the behaviour of
:mod:`scripts.single_shot_analysis`.

Populate ``CASE_MULTISHOT`` in ``case.yaml`` with the desired shot times,
for example::

    CASE_MULTISHOT: [10, 20, 30]

These timings are used to identify which project to analyse and to order
post-processing results.
"""

from pathlib import Path
import shutil

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log


def load_multishot_project(root: Path) -> Project:
    """Return the multishot project with the longest shot sequence.

    Each multishot case records every shot time in ``CASE_MULTISHOT``.
    This helper inspects the length of that list for all projects under
    ``root`` and returns the one with the most entries. Projects missing a
    valid ``CASE_MULTISHOT`` list are ignored.

    Parameters
    ----------
    root:
        Directory containing multishot projects.

    Returns
    -------
    Project
        Loaded :class:`~glacium.api.Project` instance.
    """

    pm = ProjectManager(root)
    uids = pm.list_uids()
    if not uids:
        raise FileNotFoundError(f"No projects found in {root}")

    best_uid = uids[0]
    best_len = -1
    for uid in uids:
        try:
            proj = Project.load(root, uid)
            timings = proj.get("CASE_MULTISHOT") or []
            length = len(timings) if isinstance(timings, list) else -1
        except Exception:
            length = -1
        if length > best_len:
            best_uid = uid
            best_len = length

    return Project.load(root, best_uid)


def analyze_project(proj: Project, out_dir: Path) -> None:
    """Collect basic analysis artefacts for a multishot project."""

    out_dir.mkdir(parents=True, exist_ok=True)
    ms_dir = proj.root / "analysis" / "MULTISHOT"

    gif = ms_dir / "ice_growth.gif"
    if gif.exists():
        shutil.copy2(gif, out_dir / gif.name)


def main(base_dir: Path | str = Path("")) -> None:
    """Entry point used by other scripts and the command line."""

    base = Path(base_dir)
    root = base / "05_multishot"

    try:
        proj = load_multishot_project(root)
    except FileNotFoundError as err:
        log.error(str(err))
        return

    analyze_project(proj, base / "06_multishot_results")


if __name__ == "__main__":
    main()

