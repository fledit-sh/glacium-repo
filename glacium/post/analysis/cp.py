from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

__all__ = ["read_tec_ascii", "compute_cp", "plot_cp"]


def _parse_variable_names(lines: List[str]) -> Tuple[List[str], int]:
    for idx, ln in enumerate(lines):
        if ln.lstrip().upper().startswith("VARIABLES"):
            return re.findall(r'"([^"\\]+)"', ln), idx
    raise ValueError("VARIABLES line not found – wrong format?")


def _parse_zone_nodecount(lines: List[str], start_idx: int) -> Tuple[int, int]:
    rgx = re.compile(r"ZONE.*N\s*=\s*(\d+)", re.IGNORECASE)
    for idx in range(start_idx, len(lines)):
        m = rgx.search(lines[idx])
        if m:
            return int(m.group(1)), idx
    raise ValueError("ZONE with N= not found – incomplete header")


def read_tec_ascii(fname: str | Path) -> pd.DataFrame:
    """Return knot data of first zone from Tecplot ASCII file."""
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

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    x_col = [c for c in df.columns if c.strip().upper() == "X"][0]
    p_col = [c for c in df.columns if "pressure" in c.lower()][0]
    return df.dropna(subset=[x_col, p_col])


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
        raise KeyError("column 'wall distance' missing – export without distance?")
    wd_col = wd_candidates[0]

    wd_abs = df[wd_col].abs()
    surf = df[wd_abs <= wall_tol].copy()

    if surf.empty:
        wd_min = wd_abs.dropna().min()
        if np.isnan(wd_min):
            raise RuntimeError("wall distance column only NaNs – cannot locate surface")
        rel_tol_val = wd_min * rel_pct / 100.0
        surf = df[wd_abs <= wd_min + rel_tol_val].copy()
        print(
            f"Fallback: no points within {wall_tol:g} m, rel_tol={rel_pct}% of wd_min={wd_min:.3e} -> {rel_tol_val:.3e} m (n={len(surf)})"
        )

    if surf.empty:
        raise RuntimeError("No near-wall points found – check export or tolerances")

    p_col = [c for c in df.columns if "pressure" in c.lower()][0]
    x_col = [c for c in df.columns if c.strip().upper() == "X"][0]
    y_col = [c for c in df.columns if c.strip().upper() == "Y"][0]

    q_inf = 0.5 * rho_inf * u_inf ** 2
    surf["Cp"] = (surf[p_col] - p_inf) / q_inf
    surf["x_c"] = surf[x_col] / chord
    surf["Surface"] = np.where(surf[y_col] >= 0, "Upper", "Lower")

    return surf.sort_values(["Surface", "x_c"])[["x_c", "Cp", "Surface"]]


def plot_cp(df: pd.DataFrame, outfile: str | Path, upper_label: str = "Upper", lower_label: str = "Lower") -> Path:
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
    outfile = Path(outfile)
    fig.savefig(outfile, dpi=300)
    plt.close(fig)
    return outfile
