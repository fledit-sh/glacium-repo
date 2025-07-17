#!/usr/bin/env python3
"""
TEC‑PLOT → Eisdicken‑Post‑Processor
==================================
Erzeugt den **Ice‑Thickness‑Verlauf t_ice(x/c)** aus einer Tecplot‑ASCII‑Datei,
die eine *Wall‑Zone* („WALL_XXXX“) der Vereisungs­simulation enthält.

Beispielaufruf
--------------
```bash
python tecplot_ice_plot.py wall_2000.dat --c 1.0 --unit mm
```
Ergebnis
~~~~~~~~
* `ice_data.csv`  – Tabelle (x/c, t_ice, Surface)
* `ice_plot.png`  – Plot Ober‑ & Unterseite (t_ice vs. x/c)

Optionen
~~~~~~~~
* `--c`          Chordlänge [m] (Required)
* `--unit`       `m`, `mm` oder `micron` → Umrechnungsfaktor für Plot & CSV
* `--upper_label`/`--lower_label`  Legendeneinträge

Dependencies: **numpy, pandas, matplotlib**
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Tecplot ASCII Reader – liest exakt N Knotenzeilen der ersten Wall‑Zone
# ---------------------------------------------------------------------------

def _parse_variable_names(lines: List[str]) -> Tuple[List[str], int]:
    for idx, ln in enumerate(lines):
        if ln.lstrip().upper().startswith("VARIABLES"):
            return re.findall(r'"([^"\\]+)"', ln), idx
    raise ValueError("VARIABLES line not found – wrong format?")


def _parse_zone_nodecount(lines: List[str], start_idx: int) -> Tuple[int, int]:
    zone_rgx = re.compile(r"ZONE.*T\s*=\s*\"WALL", re.IGNORECASE)
    n_rgx = re.compile(r"N\s*=\s*(\d+)")
    for idx in range(start_idx, len(lines)):
        if zone_rgx.search(lines[idx]):
            m = n_rgx.search(lines[idx])
            if not m:
                raise ValueError("Wall zone found but N= missing.")
            return int(m.group(1)), idx
    raise ValueError("No WALL_* zone with N= found – check Tecplot export.")


def read_wall_zone(fname: str | Path) -> pd.DataFrame:
    """Return DataFrame with knotendata of first WALL_* zone."""
    with open(fname, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    var_names, var_idx = _parse_variable_names(lines)
    n_nodes, zone_idx = _parse_zone_nodecount(lines, var_idx + 1)

    # find first numeric data row after zone header
    data_start = zone_idx + 1
    while data_start < len(lines):
        token = lines[data_start].lstrip()
        if token and (token[0].isdigit() or token[0] == "-"):
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

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    x_col = [c for c in df.columns if c.strip().upper() == "X"][0]
    y_col = [c for c in df.columns if c.strip().upper() == "Y"][0]
    ice_candidates = [c for c in df.columns if "ice thickness" in c.lower() and "instant" not in c.lower()]
    if not ice_candidates:
        raise KeyError("Spalte 'Ice thickness' nicht gefunden.")
    ice_col = ice_candidates[0]

    return df[[x_col, y_col, ice_col]].rename(columns={x_col: "X", y_col: "Y", ice_col: "t_ice"})

# ---------------------------------------------------------------------------
# Processing & Plot
# ---------------------------------------------------------------------------

def to_unit(arr: pd.Series, unit: str) -> Tuple[pd.Series, str]:
    unit = unit.lower()
    if unit == "m":
        return arr, "m"
    if unit == "mm":
        return arr * 1e3, "mm"
    if unit in {"micron", "µm", "um"}:
        return arr * 1e6, "µm"
    raise ValueError("unit must be m|mm|micron")


def process(df: pd.DataFrame, chord: float, unit: str) -> pd.DataFrame:
    df = df.copy()
    df["x_c"] = df["X"] / chord
    df["Surface"] = np.where(df["Y"] >= 0, "Upper", "Lower")
    df["t_ice"], unit_out = to_unit(df["t_ice"], unit)
    return df.sort_values(["Surface", "x_c"])[["x_c", "t_ice", "Surface"]], unit_out


def plot_ice(df: pd.DataFrame, unit: str, outfile: Path, ulab: str, llab: str):
    fig, ax = plt.subplots(figsize=(6, 4))
    for surf, label in [("Upper", ulab), ("Lower", llab)]:
        sub = df[df["Surface"] == surf]
        ax.plot(sub["x_c"], sub["t_ice"], "o-", ms=3, lw=0.8, label=label)
    ax.set_xlabel(r"$x/c$")
    ax.set_ylabel(fr"Ice thickness [{unit}]")
    ax.grid(True, ls=":", lw=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(outfile, dpi=300)
    plt.close(fig)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Compute & plot ice thickness from Tecplot WALL zone.")
    ap.add_argument("input", help="Tecplot ASCII file containing WALL_* zone")
    ap.add_argument("--c", type=float, required=True, help="Chord length [m]")
    ap.add_argument("--unit", default="mm", help="Output unit: m|mm|micron (default mm)")
    ap.add_argument("--upper_label", default="Upper", help="Legend label upper surface")
    ap.add_argument("--lower_label", default="Lower", help="Legend label lower surface")
    args = ap.parse_args()

    raw = read_wall_zone(args.input)
    proc, unit_out = process(raw, args.c, args.unit)

    csv_path = Path("ice_data.csv")
    png_path = Path("ice_plot.png")
    proc.to_csv(csv_path, index=False)
    plot_ice(proc, unit_out, png_path, args.upper_label, args.lower_label)
    print(f"✔ Eisdicken‑Daten→ {csv_path} - > {png_path}")


if __name__ == "__main__":
    main()
