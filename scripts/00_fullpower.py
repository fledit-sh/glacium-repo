from __future__ import annotations

"""Drive the full power study scripts.

Results are written into a study directory. If no name is provided,
the default ``C02_V50_T2_L052`` is used.
"""

from pathlib import Path
import argparse
import subprocess

DEFAULT_STUDY_NAME = "C0200_V50_T4_L0547"

SCRIPTS = [
    "01_full_power_creation.py",
    "02_full_power_gci.py",
    "05_multishot_creation.py",
    "06_multishot_analysis.py",
    "07_aoa0_projects.py",
    "08_clean_sweep_creation.py",
    "09_clean_sweep_analysis.py",
    "10_iced_sweep_creation.py",
    "11_iced_sweep_analysis.py",
    "12_polar_compare.py",
]


def main(study_name: str | None = None) -> None:
    if study_name is None:
        study_name = DEFAULT_STUDY_NAME

    base_dir = Path(study_name)
    base_dir.mkdir(parents=True, exist_ok=True)

    scripts_dir = Path(__file__).resolve().parent
    for script in SCRIPTS:
        subprocess.run(
            ["python", str(scripts_dir / script)],
            check=True,
            cwd=base_dir,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full power study")
    parser.add_argument(
        "study_name",
        nargs="?",
        help="name of the study directory below scripts",
    )
    args = parser.parse_args()
    main(args.study_name)
