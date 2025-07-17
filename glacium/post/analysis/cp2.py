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
from typing import List, Tuple

import re
import numpy as np
import pandas as pd
import trimesh
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# ---------- Tecplot-Utilities (aus cp.py) -----------------------------
# ----------------------------------------------------------------------
def _parse_variable_names(lines: List[str]) -> Tuple[List[str], int]:
    for idx, ln in enumerate(lines):
        if ln.lstrip().upper().startswith("VARIABLES"):
            return re.findall(r'"([^"\\]+)"', ln), idx
    raise ValueError("VARIABLES line not found")

def _parse_zone_nodecount(lines: List[str], start_idx: int) -> Tuple[int, int]:
    rgx = re.compile(r"ZONE.*N\s*=\s*(\d+)", re.IGNORECASE)
    for idx in range(start_idx, len(lines)):
        m = rgx.search(lines[idx]);  # type: ignore
        if m:
            return int(m.group(1)), idx
    raise ValueError("ZONE with N= not found")

def read_tec_ascii(fname: str | Path) -> pd.DataFrame:
    with open(fname, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    var_names, var_idx = _parse_variable_names(lines)
    n_nodes, zone_idx = _parse_zone_nodecount(lines, var_idx + 1)

    # Datenblöcke überspringen bis zu den Zahlen
    data_start = zone_idx + 1
    while data_start < len(lines):
        first = lines[data_start].lstrip()
        if first and (first[0].isdigit() or first[0] == "-"):
            break
        data_start += 1

    df = pd.read_csv(
        fname,
        sep=r"\s+",
        header=None,
        names=var_names,
        skiprows=data_start,
        nrows=n_nodes,
        engine="c",
    )
    df = df.apply(pd.to_numeric, errors="coerce")
    # Nur X-, Y- und Druckspalte prüfen
    x_col = [c for c in df.columns if c.strip().upper() == "X"][0]
    p_col = [c for c in df.columns if "pressure" in c.lower()][0]
    return df.dropna(subset=[x_col, p_col])

def compute_cp(
    df: pd.DataFrame,
    p_inf: float,
    rho_inf: float,
    u_inf: float,
    wall_tol: float,
    rel_pct: float,
) -> pd.DataFrame:
    wd_candidates = [c for c in df.columns if c.lower().startswith("wall distance")]
    if not wd_candidates:
        raise KeyError("'wall distance' column fehlt")
    wd_col = wd_candidates[0]

    wd_abs = df[wd_col].abs()
    surf = df[wd_abs <= wall_tol].copy()
    if surf.empty:
        wd_min = wd_abs.dropna().min()
        surf = df[wd_abs <= wd_min * (1 + rel_pct / 100.0)].copy()
    if surf.empty:
        raise RuntimeError("Keine Near-Wall-Punkte gefunden")

    p_col = [c for c in df.columns if "pressure" in c.lower()][0]
    q_inf = 0.5 * rho_inf * u_inf ** 2
    surf["Cp"] = (surf[p_col] - p_inf) / q_inf
    return surf[["X", "Y", "Cp"]].reset_index(drop=True)

# ----------------------------------------------------------------------
# ---------- STL-Utilities (aus ice_contours.py) -----------------------
# ----------------------------------------------------------------------
def load_stl_contour(stl_file: str | Path) -> np.ndarray:
    mesh = trimesh.load_mesh(stl_file, process=False)
    edges = mesh.edges_boundary
    # Randknoten → x-y-Koordinaten
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
        plt.plot(mapped["x"], mapped["Cp"], "-k")
        plt.gca().invert_yaxis()
        plt.xlabel("x [m]")
        plt.ylabel(r"$C_p$")
        plt.grid(ls=":")
        plt.tight_layout()
        plt.savefig(args.output.with_suffix(".png"), dpi=300)
        plt.close()

if __name__ == "__main__":  # pragma: no cover
    main()
