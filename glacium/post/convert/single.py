# glacium/post/convert/single.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from glacium.utils.logging import log

@dataclass
class SingleShotConverter:
    root: Path                               # run_FENSAP / run_DROP3D / run_ICE3D
    exe: Path = Path(r"C:\Program Files\ANSYS Inc\v251\fensapice\bin\nti2tecplot.exe")
    overwrite: bool = False

    MAP = {
        "run_FENSAP": (
            "SOLN",            # nti2tec mode
            "mesh.grid",        # name of grid file inside mesh/
            "soln",     # raw solution
            "soln.dat"  # Tecplot output
        ),
        "run_DROP3D": (
            "DROPLET",
            "mesh.grid",
            "droplet",
            "droplet.dat"
        ),
        "run_ICE3D": (
            "SWIMSOL",
            "ice.grid",
            "swimsol",
            "swimsol.dat"
        ),
    }

    # ------------------------------------------------------------------ #

    def _ensure_local_grid(self, grid_src: Path, run_dir: Path) -> str:
        """
        Make sure the grid file lives inside `run_dir`; copy if necessary.
        Returns just the file name (relative path) that nti2tec expects.
        """
        target = run_dir / grid_src.name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(grid_src, target)
        return target.name  # basename only

    def convert(self) -> Path:
        run_dir = self.root
        tag = run_dir.name
        mode, grid_name, src_name, dst_name = self.MAP[tag]


        # GRID LOOKUP
        if tag in {"run_FENSAP", "run_DROP3D"}:
            grid_src = run_dir.parent / "mesh" / grid_name  # external grid
        else:  # run_ICE3D
            grid_src = run_dir / grid_name  # already local

        src      = run_dir / src_name
        dst      = run_dir / dst_name

        if not src.exists():
            raise FileNotFoundError(src)

        if dst.exists() and not self.overwrite:
            return dst
        grid_local_name = self._ensure_local_grid(grid_src, run_dir)

        cmd = [
            str(self.exe),
            mode,
            grid_local_name,
            src_name,
            dst_name,
        ]
        # Run converter
        subprocess.run(cmd, cwd=run_dir, check=True)

        return dst
