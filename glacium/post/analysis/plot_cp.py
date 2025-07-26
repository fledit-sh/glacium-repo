"""Cp plotting colouring each segment by direction.

This module was originally written as a standalone script. The
functionality has been wrapped into :func:`plot_cp_directional` which
computes the Cp distribution from a Tecplot ASCII file and generates a
plot with line segments coloured according to their x-direction.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scipy.spatial import KDTree


def plot_cp_directional(
    infile: str | Path,
    p_inf: float,
    rho_inf: float,
    v_inf: float,
    chord: float,
    outfile: str | Path | None = None,
) -> Path | None:
    """Plot Cp versus ``x/c`` colouring each segment by direction."""
    infile = Path(infile)
    with infile.open("r") as f:
        for line in f:
            if line.lstrip().startswith("VARIABLES"):
                variables = [m.strip("\"") for m in re.findall(r"\"([^\"]+)\"", line)]
                break
        else:
            raise RuntimeError("VARIABLES line not found.")

        for line in f:
            if line.lstrip().startswith("ZONE"):
                m = re.search(r"\bN\s*=\s*(\d+)", line)
                if m is None:
                    raise RuntimeError("Could not parse N= in ZONE header.")
                n_nodes = int(m.group(1))
                break
        else:
            raise RuntimeError("ZONE header not found.")

        rows: list[list[float]] = []
        for _ in range(n_nodes):
            row = f.readline()
            if not row:
                raise RuntimeError("Unexpected EOF while reading node data.")
            row = row.replace("D+", "E+").replace("D-", "E-")
            rows.append([float(v) for v in row.split()])

    df = pd.DataFrame(rows, columns=variables)

    q_inf = 0.5 * rho_inf * v_inf ** 2
    if q_inf == 0:
        raise ValueError("q_inf is zero; check rho_inf or v_inf.")

    df["Cp"] = (df["Pressure (N/m^2)"] - p_inf) / q_inf

    wd_key = "wall distance (m)"
    if wd_key not in df.columns:
        raise KeyError(f"{wd_key!r} not found in variables.")

    wd_min = df[wd_key].min()
    wd_tol = abs(wd_min) * 1e-6 + 1e-12
    wall = df[df[wd_key] <= wd_min + wd_tol].copy()

    if wall.empty:
        raise RuntimeError("No nodes at global minimum wall distance.")

    coords = wall[["X", "Y"]].to_numpy()
    start_idx = int(np.argmin(coords[:, 0]))
    visited = np.zeros(len(coords), dtype=bool)
    order = [start_idx]
    visited[start_idx] = True
    kd = KDTree(coords)

    while visited.sum() < len(coords):
        current = order[-1]
        k_neigh = min(8, len(coords) - visited.sum())
        _, idxs = kd.query(coords[current], k=k_neigh)
        if np.isscalar(idxs):
            idxs = [idxs]
        next_idx = next((i for i in idxs if not visited[i]), None)
        if next_idx is None:
            remaining = np.where(~visited)[0]
            deltas = coords[remaining] - coords[current]
            next_idx = remaining[np.argmin(np.einsum("ij,ij->i", deltas, deltas))]
        order.append(next_idx)
        visited[next_idx] = True

    wall_sorted = wall.iloc[order].reset_index(drop=True)

    xc = wall_sorted["X"].to_numpy() / chord
    cp = wall_sorted["Cp"].to_numpy()

    dx = np.diff(xc)
    colours = ["red" if d > 0 else "black" for d in dx]
    segments = [((xc[i], cp[i]), (xc[i + 1], cp[i + 1])) for i in range(len(dx))]

    fig, ax = plt.subplots(figsize=(8, 4))
    lc = LineCollection(segments, colors=colours, linewidths=1.0)
    ax.add_collection(lc)
    ax.invert_yaxis()
    ax.set_xlabel("x/c [-]")
    ax.set_ylabel("Cp [-]")
    ax.set_title("Cp vs x/c")
    ax.grid(True)
    ax.set_xlim(-0.2, 1)
    ax.set_ylim(1.5, -1.5)
    fig.tight_layout()

    if outfile is not None:
        outfile = Path(outfile)
        fig.savefig(outfile, dpi=1200)
        plt.close(fig)
        return outfile
    else:
        plt.show()
        return None


def main() -> None:
    """CLI entry point for :func:`plot_cp_directional`."""
    import argparse

    ap = argparse.ArgumentParser(description="Plot Cp with direction-coloured segments")
    ap.add_argument("infile", type=Path, help="Tecplot ASCII file")
    ap.add_argument("--p-inf", type=float, required=True, help="Free-stream pressure [Pa]")
    ap.add_argument("--rho-inf", type=float, required=True, help="Free-stream density [kg/m^3]")
    ap.add_argument("--v-inf", type=float, required=True, help="Free-stream velocity [m/s]")
    ap.add_argument("--chord", type=float, required=True, help="Chord length [m]")
    ap.add_argument("-o", "--output", type=Path, help="Output PNG file")
    args = ap.parse_args()

    plot_cp_directional(args.infile, args.p_inf, args.rho_inf, args.v_inf, args.chord, args.output)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
