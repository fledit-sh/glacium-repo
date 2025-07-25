from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

from ..processor import PostProcessor
from ..artifact import ArtifactIndex
from ...utils.logging import log

@dataclass
class MultiShotConverter:
    root: Path
    exe: Path = Path("C:\Program Files\ANSYS Inc\v251\fensapice\bin\nti2tecplot.exe")
    overwrite: bool = False
    concurrency: int = 4

    PATTERNS = {
        "SOLN": ("soln.fensap.{id}", "soln.fensap.{id}.dat"),
        "DROPLET": ("droplet.drop.{id}", "droplet.drop.{id}.dat"),
        "SWIMSOL": ("swimsol.ice.{id}", "swimsol.ice.{id}.dat"),
    }

    def _ensure_local_grid(self, shot: str) -> str:
        """Return the grid file name for ``shot`` and copy if missing."""
        log.info(f"Ensure local grid for {shot}")

        grid = self.root / f"grid.ice.{shot}"
        if shot == "000001" and not grid.exists():
            src = self.root.parent / "mesh" / "mesh.grid"
            if src.exists():
                grid.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, grid)
        return grid.name

    def _convert_one(self, shot: str) -> list[Path]:
        """Convert all files for a single ``shot``."""
        grid_std = self._ensure_local_grid(shot)
        grid_ice = f"ice.grid.ice.{shot}"
        out: list[Path] = []
        for mode, (src_tpl, dst_tpl) in self.PATTERNS.items():
            src = self.root / src_tpl.format(id=shot)
            dst = self.root / dst_tpl.format(id=shot)
            if not src.exists():
                continue
            if dst.exists() and not self.overwrite:
                out.append(dst)
                continue
            grid_name = grid_std if mode in {"SOLN", "DROPLET"} else grid_ice
            cmd = [
                str(self.exe),
                mode,
                grid_name,
                src_tpl.format(id=shot),
                dst_tpl.format(id=shot),
            ]
            subprocess.run(cmd, cwd=self.root, check=True)
            out.append(dst)

        return out

    def convert_all(self) -> ArtifactIndex:
        shots = sorted({p.suffix[-6:] for p in self.root.glob("*.??????")})
        shots = shots[1:len(shots)-1]
        log.info(shots)
        with ThreadPoolExecutor(max_workers=len(shots)) as ex:
            list(ex.map(self._convert_one, shots))
        return PostProcessor(self.root.parent).index
