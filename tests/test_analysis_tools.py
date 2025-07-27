import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
import numpy as np
import pandas as pd
import trimesh
import pytest

from glacium.post.analysis.cp import compute_cp
from glacium.post.analysis.ice_thickness import process_wall_zone
from glacium.post.analysis.ice_contours import load_contours
from glacium.post.analysis import (
    load_stl_contour,
    resample_contour,
    map_cp_to_contour,
    momentum_coefficient,
)


def test_compute_cp_basic():
    p_inf = 100000.0
    rho_inf = 1.0
    u_inf = 20.0
    q_inf = 0.5 * rho_inf * u_inf ** 2
    cp_vals = [-1.0, 0.5, -0.5, 1.0]
    df = pd.DataFrame(
        {
            "X": [1.0, 0.0, 0.0, 1.0],
            "Y": [0.2, -0.1, 0.1, -0.2],
            "Pressure": [p_inf + q_inf * c for c in cp_vals],
            "Wall Distance": [0.0] * 4,
        }
    )
    res = compute_cp(df, p_inf, rho_inf, u_inf, 1.0, 0.01, 2.0)
    assert sorted(res["x_c"]) == [0.0, 0.0, 1.0, 1.0]
    assert sorted(res["Cp"]) == [-1.0, -0.5, 0.5, 1.0]
    assert sorted(res["Surface"]) == ["Lower", "Lower", "Upper", "Upper"]


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


def test_load_and_resample_contour(tmp_path):
    vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float)
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    stl = tmp_path / "contour.stl"
    mesh.export(stl)

    contour = load_stl_contour(stl)
    assert contour.shape[1] == 2
    rs = resample_contour(contour, n_pts=8)
    assert rs.shape == (8, 2)
    assert np.isclose(rs[0, 0], contour[:, 0].min())


def test_map_cp_to_contour():
    contour = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    surf_df = pd.DataFrame({"X": [0.0, 2.0], "Y": [0.0, 0.0], "Cp": [1.0, 2.0]})
    mapped = map_cp_to_contour(contour, surf_df)
    assert list(mapped["Cp"]) == [1.0, 1.0, 2.0]


def test_momentum_coefficient():
    cp_df = pd.DataFrame(
        {
            "x_c": [0.0, 0.25, 0.5, 0.75, 1.0],
            "Cp": [-1.0, -0.5, 0.0, 0.5, 0.0],
        }
    )
    cmu = momentum_coefficient(cp_df)
    assert cmu == pytest.approx(0.125)

