"""Generate multishot datasets by running ``plot_test.py`` in project folders."""

from __future__ import annotations

import argparse
import sys
import subprocess
from pathlib import Path
from typing import Iterable


def _iter_projects(multishot_root: Path) -> Iterable[Path]:
    """Yield child project directories under ``multishot_root``."""

    if not multishot_root.exists():
        return []

    return sorted(
        project
        for project in multishot_root.iterdir()
        if project.is_dir()
    )


def _has_required_inputs(project_dir: Path) -> bool:
    """Check that ``project_dir`` contains the files needed for dataset generation."""

    case_file = project_dir / "case.yaml"
    analysis_dir = project_dir / "analysis" / "MULTISHOT"
    return case_file.is_file() and analysis_dir.exists()



def main(base_dir: str | Path | None = None) -> None:
    """Generate datasets for each multishot project and the aggregate directory."""

    base_path = Path(base_dir) if base_dir is not None else Path(".")
    multishot_root = base_path / "05_multishot"

    if not multishot_root.exists():
        print(f"Multishot directory '{multishot_root}' does not exist. Nothing to do.")
        return

    dataset_script = Path(__file__).resolve().parent / "plot_test.py"
    if not dataset_script.exists():
        raise FileNotFoundError(
            "Required dataset script 'plot_test.py' is missing in the scripts directory."
        )

    for project_dir in _iter_projects(multishot_root):
        if not _has_required_inputs(project_dir):
            continue
        subprocess.run(
            [sys.executable, str(dataset_script)],
            check=True,
            cwd=project_dir,
        )

    if _has_required_inputs(multishot_root):
        subprocess.run(
            [sys.executable, str(dataset_script)],
            check=True,
            cwd=multishot_root,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate multishot datasets for individual projects and the aggregate directory."
    )
    parser.add_argument(
        "base_dir",
        nargs="?",
        default=".",
        help="Base directory containing the 05_multishot folder.",
    )
    args = parser.parse_args()
    main(args.base_dir)
