import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
import numpy as np
import pandas as pd
import trimesh

from glacium.post.analysis.ice_thickness import process_wall_zone
from glacium.post.analysis.ice_contours import load_contours


def test_process_wall_zone_unit_sort():
    df = pd.DataFrame(
        {
            "X": [1.0, 0.0, 0.0, 1.0],
            "Y": [0.2, -0.1, 0.1, -0.2],
            "t_ice": [0.001, 0.002, 0.003, 0.004],
        }
    )
    proc, unit = process_wall_zone(df, chord=1.0, unit="mm")
    assert unit == "mm"
    assert np.allclose(proc["x_c"], [0.0, 1.0, 0.0, 1.0])
    assert np.allclose(proc["t_ice"], [2.0, 4.0, 3.0, 1.0])
    assert proc["Surface"].tolist() == ["Lower", "Lower", "Upper", "Upper"]


def test_load_contours_extract(tmp_path):
    vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float)
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    stl = tmp_path / "contour1.stl"
    mesh.export(stl)

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        segs = load_contours("*.stl")
    finally:
        os.chdir(cwd)
    assert len(segs) == 1
    seg = segs[0]
    assert seg.shape[2] == 2
    pts = np.unique(seg.reshape(-1, 2), axis=0)
    exp = np.array([[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]])
    assert pts.shape[0] == 4
    for p in exp:
        assert any(np.allclose(p, q) for q in pts)
