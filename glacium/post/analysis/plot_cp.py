"""cp_vs_xc_dircolor.py
-------------------------------------------------
Plot Cp versus x/c for the body surface, colouring each line segment by **direction**:
• red   – segment moves to larger x/c (rightward)
• black – segment moves to smaller x/c (leftward)

The wall nodes are identified using the global minimum of "wall distance (m)".
Nodes are then ordered with the same nearest‑neighbour walk used previously.

Parameters to set below:
• `FILEPATH`, freestream `P_INF`, `RHO_INF`, `V_INF`
• `CHORD` – chord length for normalising x.
• `OUTPUT_PNG` – optional filename for saving the figure.

Dependencies: numpy, pandas, matplotlib, scipy.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scipy.spatial import KDTree

# ────────────────────── USER INPUT ───────────────────────────────────────────
FILEPATH = Path("soln.fensap.000016.dat")  # Tecplot ASCII file
P_INF = 101_325.0       # Freestream static pressure [Pa]
RHO_INF = 1.225         # Freestream density         [kg/m³]
V_INF = 50.0            # Freestream velocity mag.   [m/s]
CHORD = 0.431           # Chord length c [m]
OUTPUT_PNG = Path("cp_vs_xc_dircolor.png")  # set to None to skip saving
# ----------------------------------------------------------------------------

# 1 ── Read VARIABLE list & first ZONE block (nodes only) ────────────────────
with FILEPATH.open("r") as f:
    # VARIABLES
    for line in f:
        if line.lstrip().startswith("VARIABLES"):
            variables = [m.strip("\"") for m in re.findall(r"\"([^\"]+)\"", line)]
            break
    else:
        raise RuntimeError("VARIABLES line not found.")

    # ZONE
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

# 2 ── Compute Cp ─────────────────────────────────────────────────-----------
q_inf = 0.5 * RHO_INF * V_INF ** 2
if q_inf == 0:
    raise ValueError("q_inf is zero; check RHO_INF or V_INF.")

df["Cp"] = (df["Pressure (N/m^2)"] - P_INF) / q_inf

# 3 ── Select wall nodes (minimum wall distance) ───────────────────────────--
wd_key = "wall distance (m)"
if wd_key not in df.columns:
    raise KeyError(f"{wd_key!r} not found in variables.")

wd_min = df[wd_key].min()
wd_tol = abs(wd_min) * 1e-6 + 1e-12
wall = df[df[wd_key] <= wd_min + wd_tol].copy()

if wall.empty:
    raise RuntimeError("No nodes at global minimum wall distance.")

# 4 ── Order wall nodes with nearest‑neighbour walk ─────────────────────────-
coords = wall[["X", "Y"]].to_numpy()
start_idx = int(np.argmin(coords[:, 0]))  # most upstream
visited = np.zeros(len(coords), dtype=bool)
order = [start_idx]
visited[start_idx] = True
kd = KDTree(coords)

while visited.sum() < len(coords):
    current = order[-1]
    k_neigh = min(8, len(coords) - visited.sum())
    dists, idxs = kd.query(coords[current], k=k_neigh)
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

# 5 ── Prepare x/c, Cp and colours by direction ─────────────────────────────
xc = wall_sorted["X"].to_numpy() / CHORD
cp = wall_sorted["Cp"].to_numpy()

# Determine colour per segment based on delta x
dx = np.diff(xc)
colours = ["red" if d > 0 else "black" for d in dx]
segments = [((xc[i], cp[i]), (xc[i+1], cp[i+1])) for i in range(len(dx))]

# 6 ── Plot Cp(x/c) with colour‑coded segments ─────────────────────────------
fig, ax = plt.subplots(figsize=(8, 4))

lc = LineCollection(segments, colors=colours, linewidths=1.0)
ax.add_collection(lc)

# add markers for visibility
#ax.scatter(xc, cp, color="k", s=6, zorder=2)

ax.invert_yaxis()
ax.set_xlabel("x/c [-]")
ax.set_ylabel("Cp [-]")
ax.set_title("Cp vs x/c")
ax.grid(True)

# Adjust x/y limits
ax.set_xlim(xc.min(), xc.max())
ax.set_ylim(cp.max(), cp.min())

plt.tight_layout()

if OUTPUT_PNG is not None:
    fig.savefig(OUTPUT_PNG, dpi=1200)
    print(f"Saved figure → {OUTPUT_PNG}")

plt.show()
