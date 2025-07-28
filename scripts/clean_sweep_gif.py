from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log

IMAGE_NAME = "Pressure [N_m^2]_zoom.png"

def load_frames(root: Path) -> list[tuple[float, Path]]:
    """Return AoA and image path tuples for all completed runs under ``root``."""
    pm = ProjectManager(root)
    frames: list[tuple[float, Path]] = []
    for uid in pm.list_uids():
        try:
            proj = Project.load(root, uid)
        except FileNotFoundError:
            continue
        try:
            aoa = float(proj.get("CASE_AOA"))
        except Exception:
            continue
        img = proj.root / "analysis" / "FENSAP" / IMAGE_NAME
        if img.exists():
            frames.append((aoa, img))
        else:
            log.warning(f"Missing image for {uid}: {img}")
    return frames

def make_gif(frames: list[tuple[float, Path]], outfile: Path, fps: int = 2) -> None:
    """Create GIF ``outfile`` from ``frames`` sorted by AoA."""
    if not frames:
        log.error("No images found to create GIF.")
        return
    frames.sort(key=lambda t: t[0])
    images = [Image.open(p) for _, p in frames]
    first, *rest = images
    outfile.parent.mkdir(parents=True, exist_ok=True)
    first.save(outfile, save_all=True, append_images=rest,
               duration=int(1000 / fps), loop=0)
    for im in images:
        im.close()
    log.success(f"GIF written to {outfile}")

def main() -> None:
    root = Path("CleanSweep")
    out_dir = Path("aoa_sweep_results")
    frames = load_frames(root)
    make_gif(frames, out_dir / "pressure_zoom.gif")

if __name__ == "__main__":
    main()
