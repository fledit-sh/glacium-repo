from __future__ import annotations

from pathlib import Path

import full_power_creation
import full_power_gci
import clean_sweep_creation
import clean_sweep_analysis
import multishot_creation
import multishot_analysis
import iced_sweep_creation
import iced_sweep_analysis
import polar_compare


def main(base_dir: str = "Study1") -> None:
    study_root = Path(base_dir)

    case_vars = {
        "CASE_CHARACTERISTIC_LENGTH": 0.431,
        "CASE_VELOCITY": 20,
        "CASE_ALTITUDE": 100,
        "CASE_TEMPERATURE": 263.15,
        "CASE_AOA": 0,
        "CASE_YPLUS": 0.3,
    }

    full_power_creation.main(study_root, case_vars=case_vars)
    full_power_gci.main(study_root)
    clean_sweep_creation.main(study_root)
    clean_sweep_analysis.main(study_root)
    multishot_creation.main(study_root)
    multishot_analysis.main(study_root)
    iced_sweep_creation.main(study_root)
    iced_sweep_analysis.main(study_root)
    polar_compare.main(study_root)


if __name__ == "__main__":
    main()
