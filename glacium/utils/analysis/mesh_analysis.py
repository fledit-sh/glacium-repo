from __future__ import annotations

from pathlib import Path
from typing import Sequence
import sys

from . import postprocess_mesh_multi, postprocess_mesh_html


def mesh_analysis(cwd: Path, args: Sequence[str | Path]) -> None:
    """Run mesh screenshot and HTML report helpers.

    Parameters
    ----------
    cwd:
        Working directory supplied by :class:`~glacium.engines.py_engine.PyEngine`.
        Unused but kept for API compatibility.
    args:
        Sequence containing ``meshfile``, ``out_dir`` and ``html_file``.
        ``out_dir`` and ``html_file`` are optional.
    """
    if not args:
        raise ValueError("mesh_analysis requires a mesh file path")

    meshfile = str(args[0])
    out_dir = Path(args[1]) if len(args) > 1 else Path("analysis/MESH")
    html_file = Path(args[2]) if len(args) > 2 else out_dir / "mesh_report.html"
    out_dir.mkdir(parents=True, exist_ok=True)

    argv_backup = sys.argv
    try:
        sys.argv = [
            "postprocess_mesh_multi.py",
            meshfile,
            "--outdir",
            str(out_dir),
        ]
        postprocess_mesh_multi.main()
    finally:
        sys.argv = argv_backup

    argv_backup = sys.argv
    try:
        sys.argv = [
            "postprocess_mesh_html.py",
            meshfile,
            "-o",
            str(html_file),
            "--png-dir",
            str(out_dir),
        ]
        postprocess_mesh_html.main()
    finally:
        sys.argv = argv_backup

