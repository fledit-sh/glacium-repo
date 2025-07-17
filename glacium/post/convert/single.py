from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass
class SingleShotConverter:
    root: Path
    exe: Path = Path("nti2tecplot.exe")
    overwrite: bool = False

    MAP = {
        "run_FENSAP": ("SOLN", "grid.ice", "soln.fensap", "soln.fensap.dat"),
        "run_DROP3D": ("DROPLET", "grid.ice", "droplet.drop", "droplet.drop.dat"),
        "run_ICE3D": ("SWIMSOL", "grid.ice", "swimsol.ice", "swimsol.ice.dat"),
    }

    def convert(self) -> Path:
        run_dir = self.root.name
        mode, grid_name, src_name, dst_name = self.MAP[run_dir]
        grid = self.root.parent / "mesh" / grid_name
        src = self.root / src_name
        dst = self.root / dst_name
        if dst.exists() and not self.overwrite:
            return dst
        subprocess.run([str(self.exe), mode, str(grid), str(src), str(dst)], check=True)
        return dst
