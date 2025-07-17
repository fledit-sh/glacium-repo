#!/usr/bin/env python3
"""
====================================================
Robustes Skript, das selbst bei **fehlender Wall‑Zone** die dem Profil
erstellt.Behobene Bugs:

* **x/y‑Spaltenerkennung**: kein Namens‑Clash mit `c` (Chordlänge).
* **surf.empty** ist eine *Property*, kein Call.

------------------------------------------------------------
CLI‑Beispiel
------------
```bash
python tecplot_cp_plot.py soln.fensap.000014.dat \
        --p_inf 101325 --rho_inf 1.225 --u_inf 70 --c 1.0 \
        --wall_tol 1e-6   # erst absolute, dann rel‑Fallback falls nötig
```

* `cp_data.csv` – Rohdaten (x/c, Cₚ, Surface)
* `cp_plot.png` – invertierter Cₚ‑Plot

------------------------------------------------------------
Dependencies
------------
`numpy`, `pandas`, `matplotlib`
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# Tecplot‑ASCII‑Reader – liest exakt N Knotenzeilen der ersten ZONE
# ----------------------------------------------------------------------------

def _parse_variable_names(lines: List[str]) -> Tuple[List[str], int]:
    for idx, ln in enumerate(lines):
        if ln.lstrip().upper().startswith("VARIABLES"):
            return re.findall(r'"([^"]+)"', ln), idx
    raise ValueError("VARIABLES‑Zeile nicht gefunden – falsches Format?")


def _parse_zone_nodecount(lines: List[str], start_idx: int) -> Tuple[int, int]:
    rgx = re.compile(r"ZONE.*N\s*=\s*(\d+)", re.IGNORECASE)
    for idx in range(start_idx, len(lines)):
        m = rgx.search(lines[idx])
        if m:
            return int(m.group(1)), idx
    raise ValueError("ZONE mit N=… nicht gefunden – Header unvollständig.")


def read_tec_ascii(fname: str | Path) -> pd.DataFrame:
    """Liest Knotendaten (keine Konnektivität) in DataFrame."""
    with open(fname, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    var_names, var_idx = _parse_variable_names(lines)
    n_nodes, zone_idx = _parse_zone_nodecount(lines, var_idx + 1)

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
        dtype=str,
    )

    # numerisch konvertieren
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # NaNs in X oder Pressure → Zeile löschen
    x_col = [c for c in df.columns if c.strip().upper() == "X"][0]
    p_col = [c for c in df.columns if "pressure" in c.lower()][0]
    return df.dropna(subset=[x_col, p_col])

# ----------------------------------------------------------------------------
# Cₚ‑Berechnung
# ----------------------------------------------------------------------------

def compute_cp(
    df: pd.DataFrame,
    p_inf: float,
    rho_inf: float,
    u_inf: float,
    chord: float,
    wall_tol: float,
    rel_pct: float,
) -> pd.DataFrame:
    wd_candidates = [c for c in df.columns if c.lower().startswith("wall distance")]
    if not wd_candidates:
        raise KeyError("Spalte 'wall distance' nicht gefunden – Export ohne Wandabstand?")
    wd_col = wd_candidates[0]

    wd_abs = df[wd_col].abs()
    surf = df[wd_abs <= wall_tol].copy()

    if surf.empty:
        wd_min = wd_abs.dropna().min()
        if np.isnan(wd_min):
            raise RuntimeError("'wall distance' besteht nur aus NaNs – kann Oberfläche nicht bestimmen.")
        rel_tol_val = wd_min * rel_pct / 100.0
        surf = df[wd_abs <= wd_min + rel_tol_val].copy()
        print(
            f"⚠︎ Fallback: keine Punkte innerhalb {wall_tol:g} m, "
            f"rel_tol={rel_pct}% von wd_min={wd_min:.3e} → {rel_tol_val:.3e} m (n={len(surf)})"
        )

    if surf.empty:
        raise RuntimeError("Keine Wand‑nahen Punkte gefunden – überprüfe Export oder Toleranzen.")

    # Spalten
    p_col = [c for c in df.columns if "pressure" in c.lower()][0]
    x_col = [c for c in df.columns if c.strip().upper() == "X"][0]
    y_col = [c for c in df.columns if c.strip().upper() == "Y"][0]

    q_inf = 0.5 * rho_inf * u_inf ** 2
    surf["Cp"] = (surf[p_col] - p_inf) / q_inf
    surf["x_c"] = surf[x_col] / chord
    surf["Surface"] = np.where(surf[y_col] >= 0, "Upper", "Lower")

    return surf.sort_values(["Surface", "x_c"])[["x_c", "Cp", "Surface"]]

# ----------------------------------------------------------------------------
# Plot
# ----------------------------------------------------------------------------

def plot_cp(df: pd.DataFrame, outfile: Path, upper_label: str, lower_label: str):
    fig, ax = plt.subplots(figsize=(6, 4))
    for surf, label in [("Upper", upper_label), ("Lower", lower_label)]:
        sub = df[df["Surface"] == surf]
        ax.plot(sub["x_c"], sub["Cp"], "o-", markersize=3, linewidth=0.8, label=label)
    ax.invert_yaxis()
    ax.set_xlabel(r"$x/c$")
    ax.set_ylabel(r"$C_p$")
    ax.grid(True, ls=":", lw=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(outfile, dpi=300)
    plt.close(fig)

# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Compute and plot C_p from Tecplot volume zones (wall zone optional).")
    ap.add_argument("input", help="Tecplot ASCII file (.dat/.tec)")
    ap.add_argument("--p_inf", type=float, required=True, help="Freestream static pressure [Pa]")
    ap.add_argument("--rho_inf", type=float, required=True, help="Freestream density [kg/m^3]")
    ap.add_argument("--u_inf", type=float, required=True, help="Freestream velocity [m/s]")
    ap.add_argument("--c", type=float, required=True, help="Chord length [m]")
    ap.add_argument("--wall_tol", type=float, default=1e-9, help="Absolute tolerance for wall distance [m]")
    ap.add_argument("--rel_pct", type=float, default=5.0, help="Relative tolerance (% of wd_min) if absolute fails")
    ap.add_argument("--upper_label", default="Upper", help="Legend label for upper surface")
    ap.add_argument("--lower_label", default="Lower", help="Legend label for lower surface")
    args = ap.parse_args()

    df = read_tec_ascii(args.input)
    surf_df = compute_cp(df, args.p_inf, args.rho_inf, args.u_inf, args.c, args.wall_tol, args.rel_pct)

    csv_path = Path("cp_data.csv")
    png_path = Path("cp_plot.png")
    surf_df.to_csv(csv_path, index=False)
    plot_cp(surf_df, png_path, args.upper_label, args.lower_label)
    print(f"✔ C_p‑Daten → {csv_path}\n✔ Plot      → {png_path}")


if __name__ == "__main__":
    main()
