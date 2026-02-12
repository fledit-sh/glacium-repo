from .converter import Converter
from typing import Optional

class ConvergDropConverter(Converter):
    def __init__(self) -> None:
        self.ready = False
        self.ncols: int | None = None

        self.header = [
            "time_step",
            "newton_iteration",
            "cpu_time",
            "overall_residual_drop",
            "total_beta_drop",
            "change_in_total_beta_drop",
            "alpha_residual_drop",
            "momentum_residual_drop",
            "drop_diameter_residual",
            "droplet_mass_deficit_pct",
        ]

    def check(self, cols: list[str], raw: str) -> None:
        if self.ncols is None:
            self.ncols = len(self.header)

        if len(cols) != self.ncols:
            raise ValueError(
                f"Data column mismatch: expected={self.ncols} got={len(cols)}. Line: {raw}"
            )

    def emit(self) -> str:
        self.ready = True
        return ",".join(self.header)

    def feed_line(self, line: str) -> Optional[str]:
        raw = line.strip()
        if not raw:
            return None

        if raw.startswith("#"):
            return None

        cols = raw.split()
        self.check(cols, raw)

        if not self.ready:
            return self.emit()

        return ",".join(cols)