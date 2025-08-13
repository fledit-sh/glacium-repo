from __future__ import annotations

from pathlib import Path
import yaml
from PIL import Image

from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log


def collect_images(root: Path) -> list[tuple[float, Path]]:
    """Return list of (AoA, image_path) for all projects under ``root``."""
    pm = ProjectManager(root)
    images: list[tuple[float, Path]] = []
    for uid in pm.list_uids():
        case_file = root / uid / "case.yaml"
        cfg_file = root / uid / "_cfg" / "global_config.yaml"
        aoa_val = None
        if case_file.exists():
            try:
                aoa_val = yaml.safe_load(case_file.read_text()).get("CASE_AOA")
            except Exception:
                pass
        if aoa_val is None and cfg_file.exists():
            try:
                aoa_val = yaml.safe_load(cfg_file.read_text()).get("CASE_AOA")
            except Exception:
                pass
        if aoa_val is None:
            continue
        try:
            aoa = float(aoa_val)
        except Exception:
            continue

        img = root / uid / "analysis" / "FENSAP" / "Pressure [N_m^2]_zoom.png"
        if not img.exists():
            alt = root / uid / "analysis" / "FENSAP" / "p_zoom.png"
            if alt.exists():
                img = alt
        if img.exists():
            images.append((aoa, img))
    images.sort(key=lambda t: t[0])
    return images


def create_gif(images: list[tuple[float, Path]], outfile: Path, *, duration: int = 500) -> Path:
    """Create GIF from ``images`` and save to ``outfile``."""
    if not images:
        log.error("No images found for GIF creation.")
        return outfile

    frames = [Image.open(p) for _, p in images]
    outfile.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        outfile,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
    )
    for f in frames:
        f.close()
    log.success(f"Wrote GIF to {outfile}")
    return outfile


def main() -> None:
    root = Path("07_clean_sweep")
    images = collect_images(root)
    create_gif(images, Path("08_clean_sweep_results") / "pressure_zoom.gif")


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
