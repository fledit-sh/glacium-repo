"""Analyse multishot projects generated in the full power study.

Key Functions
-------------
* :func:`load_multishot_project` – locate the project with the longest
  ``CASE_MULTISHOT`` list.
* :func:`analyze_project` – gather basic artefacts for that project.
* :func:`main` – command line entry point.

Inputs
------
base_dir : Path | str, optional
    Base directory containing ``05_multishot``.

Outputs
-------
Files such as ``ice_growth.gif`` and per-shot ``plots/curve_s.pdf`` copied to
``06_multishot_results``.

Usage
-----
``python scripts/06_multishot_analysis.py``

For a complete workflow example see ``docs/full_power_study.rst``.

The shot times should be listed under ``CASE_MULTISHOT`` in ``case.yaml``,
for example::

    CASE_MULTISHOT: [10, 20, 30]
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

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
    """Collect analysis artefacts for a multishot project.

    Besides copying ``ice_growth.gif``, each shot subdirectory containing a
    ``merged.dat`` file is processed with ``glacium.post.multishot.plot_s`` to
    generate ``plots/curve_s.pdf``. The populated shot directories are copied to
    ``out_dir``.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    ms_dir = proj.root / "analysis" / "MULTISHOT"

    gif = ms_dir / "ice_growth.gif"
    if gif.exists():
        shutil.copy2(gif, out_dir / gif.name)

    for shot_dir in ms_dir.iterdir():
        merged = shot_dir / "merged.dat"
        if not merged.exists():
            continue

        plots_pdf = shot_dir / "plots" / "curve_s.pdf"
        plots_pdf.parent.mkdir(parents=True, exist_ok=True)

        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "glacium.post.multishot.plot_s",
                    str(merged),
                    str(plots_pdf),
                ],
                check=True,
            )
        except Exception as err:  # pragma: no cover - logging only
            log.error(f"plot_s failed for {merged}: {err}")

        shutil.copytree(shot_dir, out_dir / shot_dir.name, dirs_exist_ok=True)


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

