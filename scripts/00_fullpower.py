from __future__ import annotations

from pathlib import Path
import argparse
import subprocess

SCRIPTS = [
    "01_full_power_creation.py",
    "02_full_power_gci.py",
    "03_single_shot_creation.py",
    "04_single_shot_analysis.py",
    "05_multishot_creation.py",
    "06_multishot_analysis.py",
    "07_clean_sweep_creation.py",
    "08_clean_sweep_analysis.py",
    "09_iced_sweep_creation.py",
    "10_iced_sweep_analysis.py",
    "11_polar_compare.py",
]


def main(study_name: str | None = None) -> None:
    study_name = "C02_V50_T2_L052"

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
