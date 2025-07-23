from __future__ import annotations

from full_power_creation import main as create_runs
from full_power_gci import main as analyze_gci


def main() -> None:
    create_runs()
    analyze_gci()


if __name__ == "__main__":
    main()
