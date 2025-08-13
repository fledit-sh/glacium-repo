import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.clean_sweep_gif import collect_images, create_gif


def _create_project(root: Path, uid: str, aoa: float) -> None:
    proj = root / uid
    img_dir = proj / "analysis" / "FENSAP"
    img_dir.mkdir(parents=True)
    img = Image.fromarray(np.zeros((1, 1, 3), dtype=np.uint8))
    img.save(img_dir / "Pressure [N_m^2]_zoom.png")
    (proj / "case.yaml").write_text(f"CASE_AOA: {aoa}\n")


def test_collect_sorted(tmp_path):
    root = tmp_path / "07_clean_sweep"
    _create_project(root, "p1", 5)
    _create_project(root, "p2", 1)

    images = collect_images(root)
    assert [a for a, _ in images] == [1.0, 5.0]


def test_gif_written(tmp_path):
    root = tmp_path / "07_clean_sweep"
    _create_project(root, "p1", 0)
    imgs = collect_images(root)
    out = tmp_path / "08_clean_sweep_results" / "pressure_zoom.gif"
    create_gif(imgs, out)
    assert out.exists()
