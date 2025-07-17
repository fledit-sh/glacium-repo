from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor

from ..processor import PostProcessor
from ..artifact import ArtifactIndex


@dataclass
class MultiShotConverter:
    root: Path
    exe: Path = Path("nti2tecplot.exe")
    overwrite: bool = False
    concurrency: int = 4

    PATTERNS = {
        "SOLN": ("soln.fensap.{id}", "soln.fensap.{id}.dat"),
        "DROPLET": ("droplet.drop.{id}", "droplet.drop.{id}.dat"),
        "SWIMSOL": ("swimsol.ice.{id}", "swimsol.ice.{id}.dat"),
    }

    def _convert_one(self, shot: str) -> list[Path]:
        grid = self.root.parent.parent / "mesh" / f"grid.ice.{shot}"
        out: list[Path] = []
        for mode, (src_tpl, dst_tpl) in self.PATTERNS.items():
            src = self.root / src_tpl.format(id=shot)
            dst = self.root / dst_tpl.format(id=shot)
            if not src.exists():
                continue
            if dst.exists() and not self.overwrite:
                out.append(dst)
                continue
            subprocess.run([str(self.exe), mode, str(grid), str(src), str(dst)], check=True)
            out.append(dst)
        return out

    def convert_all(self) -> ArtifactIndex:
        shots = sorted({p.suffix[-6:] for p in self.root.glob("*.??????")})
        with ThreadPoolExecutor(max_workers=self.concurrency) as ex:
            list(ex.map(self._convert_one, shots))
        return PostProcessor(self.root.parent).index
