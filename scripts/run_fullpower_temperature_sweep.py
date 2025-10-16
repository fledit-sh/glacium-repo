"""Run the full power driver across a temperature/LWC sweep."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


TEMPERATURE_LWC_CASES: list[tuple[float, float]] = [
    (263.15, 0.000450),
    (268.15, 0.000591),
    (273.15, 0.000750),
]


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    case_path = repo_root / Path("glacium/config/defaults/case.yaml")
    driver = repo_root / Path("scripts/00_fullpower.py")

    case_text = case_path.read_text()

    try:
        for temp_k, lwc in TEMPERATURE_LWC_CASES:
            temp_tag = abs(int(round(temp_k - 273.15)))
            lwc_tag = f"{int(round(lwc * 1e6)):04d}"
            study_name = f"NACA23012_C0450_V50_T{temp_tag}_L{lwc_tag}_PWS4_500"

            updated_text = re.sub(
                r"^(CASE_TEMPERATURE:\s*).*$",
                rf"\1{temp_k:.2f}",
                case_text,
                flags=re.MULTILINE,
            )
            updated_text = re.sub(
                r"^(CASE_LWC:\s*).*$",
                rf"\1{lwc:.6f}",
                updated_text,
                flags=re.MULTILINE,
            )

            case_path.write_text(updated_text)

            print(
                f"Running {study_name} with temperature {temp_k:.2f} K "
                f"and LWC {lwc:.6f} kg/m^3"
            )

            subprocess.run(["python", str(driver), study_name], check=True, cwd=repo_root)
    finally:
        case_path.write_text(case_text)


if __name__ == "__main__":
    main()

