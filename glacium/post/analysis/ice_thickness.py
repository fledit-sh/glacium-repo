from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scienceplots
plt.style.use(['science', 'ieee'])

__all__ = ["read_wall_zone", "process_wall_zone", "plot_ice_thickness"]


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
    """Return DataFrame with node data of first WALL_* zone."""
    with open(fname, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    var_names, var_idx = _parse_variable_names(lines)
    n_nodes, zone_idx = _parse_zone_nodecount(lines, var_idx + 1)

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
        raise KeyError("column 'Ice thickness' not found")
    ice_col = ice_candidates[0]

    return df[[x_col, y_col, ice_col]].rename(columns={x_col: "X", y_col: "Y", ice_col: "t_ice"})


def _to_unit(arr: pd.Series, unit: str) -> tuple[pd.Series, str]:
    unit = unit.lower()
    if unit == "m":
        return arr, "m"
    if unit == "mm":
        return arr * 1e3, "mm"
    if unit in {"micron", "µm", "um"}:
        return arr * 1e6, "µm"
    raise ValueError("unit must be m|mm|micron")


def process_wall_zone(df: pd.DataFrame, chord: float, unit: str) -> tuple[pd.DataFrame, str]:
    df = df.copy()
    df["x_c"] = df["X"] / chord
    df["Surface"] = np.where(df["Y"] >= 0, "Upper", "Lower")
    df["t_ice"], unit_out = _to_unit(df["t_ice"], unit)
    return df.sort_values(["Surface", "x_c"])[["x_c", "t_ice", "Surface"]], unit_out


def plot_ice_thickness(df: pd.DataFrame, unit: str, outfile: str | Path, upper_label: str = "Upper", lower_label: str = "Lower") -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    for surf, label in [("Upper", upper_label), ("Lower", lower_label)]:
        sub = df[df["Surface"] == surf]
        ax.plot(sub["x_c"], sub["t_ice"], "o-", ms=3, lw=0.8, label=label)
    ax.set_xlabel(r"$x/c$")
    ax.set_ylabel(f"Ice thickness [{unit}]")
    ax.grid(True, ls=":", lw=0.5)
    ax.legend()
    fig.tight_layout()
    outfile = Path(outfile)
    fig.savefig(outfile, dpi=300)
    plt.close(fig)
    return outfile


def main() -> None:
    """CLI helper to visualise ice thickness distributions."""
    import argparse

    ap = argparse.ArgumentParser(description="Plot ice thickness from Tecplot surface export")
    ap.add_argument("input", type=Path, help="Tecplot ASCII file")
    ap.add_argument("--chord", type=float, required=True, help="Chord length [m]")
    ap.add_argument("-o", "--output", type=Path, default="ice_thickness.png", help="Output image file")
    ap.add_argument("-u", "--unit", default="mm", help="Output unit (m|mm|micron)")
    args = ap.parse_args()

    df = read_wall_zone(args.input)
    proc, unit = process_wall_zone(df, args.chord, args.unit)
    plot_ice_thickness(proc, unit, args.output)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
