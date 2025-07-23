#!/usr/bin/env python3
# cp_map_stl.py
"""Map pressure coefficients from Tecplot onto an STL contour.

Steps
-----
1. Read Tecplot ASCII and compute ``Cp`` (near-wall layer only).
2. Load STL profile, extract a closed contour and resample it uniformly.
3. Map ``Cp`` values onto the contour via a KD-tree.
4. Optionally plot the curve or export CSV.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import trimesh
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt

from .cp import read_tec_ascii, compute_cp

# ----------------------------------------------------------------------
# ---------- STL-Utilities (aus ice_contours.py) -----------------------
# ----------------------------------------------------------------------
def load_stl_contour(stl_file: str | Path) -> np.ndarray:
    mesh = trimesh.load_mesh(stl_file, process=False)
    edges = mesh.edges_unique[mesh.edges_unique_length == 1]
    contour_xy = mesh.vertices[np.unique(edges)][:, :2]
    return contour_xy

def resample_contour(contour: np.ndarray, n_pts: int = 500) -> np.ndarray:
    # enforce closed ordering using nearest-neighbour
    # 1) start point = minimal x
    start_idx = np.argmin(contour[:, 0])
    ordered = [contour[start_idx]]
    used = {start_idx}
    for _ in range(len(contour) - 1):
        last = ordered[-1]
        # distance to all unused points
        remain_idx = [i for i in range(len(contour)) if i not in used]
        dists = np.linalg.norm(contour[remain_idx] - last, axis=1)
        next_i = remain_idx[int(np.argmin(dists))]
        ordered.append(contour[next_i]); used.add(next_i)
    ordered = np.array(ordered)

    # arc length
    ds = np.linalg.norm(np.diff(ordered, axis=0, append=ordered[:1]), axis=1)
    s = np.concatenate(([0], np.cumsum(ds)))[:-1]
    s_new = np.linspace(0, s[-1], n_pts, endpoint=False)
    x_new = np.interp(s_new, s, ordered[:, 0])
    y_new = np.interp(s_new, s, ordered[:, 1])
    return np.vstack((x_new, y_new)).T

def map_cp_to_contour(contour_pts: np.ndarray, surf_df: pd.DataFrame) -> pd.DataFrame:
    tree = cKDTree(surf_df[["X", "Y"]].values)
    dist, idx = tree.query(contour_pts)
    mapped = pd.DataFrame({
        "x": contour_pts[:, 0],
        "y": contour_pts[:, 1],
        "Cp": surf_df["Cp"].values[idx],
        "s": np.linspace(0, 1, len(contour_pts), endpoint=False)  # normalised arc length
    })
    return mapped

# ----------------------------------------------------------------------
# ---------- CLI -------------------------------------------------------
# ----------------------------------------------------------------------
def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Map Cp data from Tecplot onto an STL contour")
    ap.add_argument("tec", type=Path, help="Tecplot ASCII file (*.dat)")
    ap.add_argument("stl", type=Path, help="STL file of the profile")
    ap.add_argument("--p-inf", type=float, required=True, help="p∞ [Pa]")
    ap.add_argument("--rho-inf", type=float, required=True, help="ρ∞ [kg/m³]")
    ap.add_argument("--u-inf", type=float, required=True, help="U∞ [m/s]")
    ap.add_argument("--wall-tol", type=float, default=1e-4, help="wall distance tolerance [m]")
    ap.add_argument("--rel-pct", type=float, default=2.0, help="relative fallback tolerance [%]")
    ap.add_argument("-n", "--npts", type=int, default=500, help="number of resample points")
    ap.add_argument("-o", "--output", type=Path, default="cp_stl.csv", help="CSV output file")
    ap.add_argument("--plot", action="store_true", help="plot Cp distribution")
    args = ap.parse_args()

    # 1) read Tecplot and compute Cp
    df = read_tec_ascii(args.tec)
    surf = compute_cp(df, args.p_inf, args.rho_inf, args.u_inf, args.wall_tol, args.rel_pct)

    # 2) load STL contour and resample
    contour = load_stl_contour(args.stl)
    contour_rs = resample_contour(contour, n_pts=args.npts)

    # 3) map Cp onto contour
    mapped = map_cp_to_contour(contour_rs, surf)
    mapped.to_csv(args.output, index=False)

    # 4) optional plot
    if args.plot:
        plt.figure(figsize=(6, 4))
        plt.plot(mapped["x"], mapped["Cp"], linestyle=None,marker=".")
        plt.gca().invert_yaxis()
        plt.xlabel("x [m]")
        plt.ylabel(r"$C_p$")
        plt.grid(ls=":")
        plt.tight_layout()
        plt.savefig(args.output.with_suffix(".png"), dpi=300)
        plt.close()

if __name__ == "__main__":  # pragma: no cover
    main()
