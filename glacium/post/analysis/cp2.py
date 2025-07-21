#!/usr/bin/env python3
# cp_map_stl.py
"""
1. Tecplot-ASCII einlesen → Cp berechnen (nur Near-Wall-Layer)
2. STL-Profil laden → geschlossene Kontur extrahieren → gleichmäßig resamplen
3. Cp-Werte per KD-Tree auf Kontur abbilden
4. Optional: Cp-Kurve plotten oder CSV exportieren
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
    # geschlossene Reihenfolge erzwingen (Nearest-Neighbor)
    # 1) Anfangspunkt = minimaler x
    start_idx = np.argmin(contour[:, 0])
    ordered = [contour[start_idx]]
    used = {start_idx}
    for _ in range(len(contour) - 1):
        last = ordered[-1]
        # Distanz zu allen unbenutzten Punkte
        remain_idx = [i for i in range(len(contour)) if i not in used]
        dists = np.linalg.norm(contour[remain_idx] - last, axis=1)
        next_i = remain_idx[int(np.argmin(dists))]
        ordered.append(contour[next_i]); used.add(next_i)
    ordered = np.array(ordered)

    # Bogenlänge
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
        "s": np.linspace(0, 1, len(contour_pts), endpoint=False)  # normierte Bogenlänge
    })
    return mapped

# ----------------------------------------------------------------------
# ---------- CLI -------------------------------------------------------
# ----------------------------------------------------------------------
def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Cp-Mapping von Tecplot auf STL-Kontur")
    ap.add_argument("tec", type=Path, help="Tecplot-ASCII-Datei (*.dat)")
    ap.add_argument("stl", type=Path, help="STL-Datei des Profils")
    ap.add_argument("--p-inf", type=float, required=True, help="p∞ [Pa]")
    ap.add_argument("--rho-inf", type=float, required=True, help="ρ∞ [kg/m³]")
    ap.add_argument("--u-inf", type=float, required=True, help="U∞ [m/s]")
    ap.add_argument("--wall-tol", type=float, default=1e-4, help="wall distance-Tol. [m]")
    ap.add_argument("--rel-pct", type=float, default=2.0, help="rel. Fallback-Tol. [%]")
    ap.add_argument("-n", "--npts", type=int, default=500, help="Resample-Punkte")
    ap.add_argument("-o", "--output", type=Path, default="cp_stl.csv", help="CSV-Ausgabe")
    ap.add_argument("--plot", action="store_true", help="Cp-Verlauf plotten")
    args = ap.parse_args()

    # 1) Tecplot lesen und Cp berechnen
    df = read_tec_ascii(args.tec)
    surf = compute_cp(df, args.p_inf, args.rho_inf, args.u_inf, args.wall_tol, args.rel_pct)

    # 2) STL-Kontur laden & resamplen
    contour = load_stl_contour(args.stl)
    contour_rs = resample_contour(contour, n_pts=args.npts)

    # 3) Cp auf Kontur mappen
    mapped = map_cp_to_contour(contour_rs, surf)
    mapped.to_csv(args.output, index=False)

    # 4) Optionaler Plot
    if args.plot:
        plt.figure(figsize=(6, 4))
        plt.plot(mapped["x"], mapped["Cp"], "-k",marker=None)
        plt.gca().invert_yaxis()
        plt.xlabel("x [m]")
        plt.ylabel(r"$C_p$")
        plt.grid(ls=":")
        plt.tight_layout()
        plt.savefig(args.output.with_suffix(".png"), dpi=300)
        plt.close()

if __name__ == "__main__":  # pragma: no cover
    main()
