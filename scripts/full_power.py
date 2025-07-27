from __future__ import annotations

from full_power_creation import main as create_runs
from full_power_gci import main as analyze_gci
from clean_sweep_creation import main as run_clean_sweep
from clean_sweep_analysis import main as analyze_clean_sweep
from multishot_creation import main as create_multishot
from multishot_analysis import main as analyze_multishot
from iced_sweep_creation import main as run_iced_sweep
from iced_sweep_analysis import main as analyze_iced_sweep
from polar_compare import main as compare_polars


def main() -> None:
    create_runs()
    analyze_gci()
    run_clean_sweep()
    analyze_clean_sweep()
    create_multishot()
    analyze_multishot()
    run_iced_sweep()
    analyze_iced_sweep()
    compare_polars()


if __name__ == "__main__":
    main()
