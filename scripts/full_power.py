from __future__ import annotations

from pathlib import Path
import argparse

from full_power_creation import main as create_runs
from full_power_gci import main as analyze_gci
from clean_sweep_creation import main as run_clean_sweep
from clean_sweep_analysis import main as analyze_clean_sweep
from single_shot_creation import main as create_single_shot
from single_shot_analysis import main as analyze_single_shot
from multishot_creation import main as create_multishot
from multishot_analysis import main as analyze_multishot
from iced_sweep_creation import main as run_iced_sweep
from iced_sweep_analysis import main as analyze_iced_sweep
from polar_compare import main as compare_polars


def main(study_name: str | None = None) -> None:
    study_name = "C02_V20_T10_L0595"

    CASE_DEFAULTS = {
        "CASE_CHARACTERISTIC_LENGTH": 0.2,
        "CASE_VELOCITY": 20,
        "CASE_ALTITUDE": 100,
        "CASE_TEMPERATURE": 263.15,
        "CASE_AOA": 0,
        "CASE_YPLUS": 0.3,
        "CASE_LWC": 0.000595,
        # Total time comes from the sum of CASE_MULTISHOT
        "CASE_MULTISHOT": [1],
    }

    base_dir = Path("") / study_name
    base_dir.mkdir(parents=True, exist_ok=True)
    case_vars = CASE_DEFAULTS

    # create_runs(base_dir, case_vars)
    # analyze_gci(base_dir)
    # create_single_shot(base_dir)
    # analyze_single_shot(base_dir)
    # run_clean_sweep(base_dir, case_vars)
    # analyze_clean_sweep(base_dir)
    create_multishot(base_dir, case_vars)
    analyze_multishot(base_dir)
    # run_iced_sweep(base_dir, case_vars)
    # analyze_iced_sweep(base_dir)
    # compare_polars(base_dir)

    # study_name = "C02_V20_T10_L0595"
    # CASE_DEFAULTS = {
    #     "CASE_CHARACTERISTIC_LENGTH": 0.2,
    #     "CASE_VELOCITY": 20,
    #     "CASE_ALTITUDE": 100,
    #     "CASE_TEMPERATURE": 263.15,
    #     "CASE_AOA": 0,
    #     "CASE_YPLUS": 0.3,
    #     "CASE_LWC": 0.00052,
    #     "CASE_MULTISHOT": [3220],  # total time from sum of CASE_MULTISHOT
    # }
    #
    # base_dir = Path("") / study_name
    # case_vars = CASE_DEFAULTS
    #
    # create_runs(base_dir, case_vars)
    # analyze_gci(base_dir)
    # create_single_shot(base_dir)
    # analyze_single_shot(base_dir)
    # run_clean_sweep(base_dir, case_vars)
    # analyze_clean_sweep(base_dir)
    # create_multishot(base_dir, case_vars)
    # analyze_multishot(base_dir)
    # run_iced_sweep(base_dir, case_vars)
    # analyze_iced_sweep(base_dir)
    # compare_polars(base_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full power study")
    parser.add_argument(
        "study_name",
        nargs="?",
        help="name of the study directory below scripts",
    )
    args = parser.parse_args()
    main(args.study_name)
