#!/usr/bin/env python3
"""
stl_dat_surface_plot.py
-----------------------

Generates *s*‑curves over an STL surface and plots variables from the first
Tecplot‑*.dat* zone. Each curve is saved as a PNG.

What’s new (2025‑07‑30)
~~~~~~~~~~~~~~~~~~~~~~~
* **Custom start point**   Choose the parametric direction explicitly.
  * `--axis pca|x|y|z`   direction used for ordering (default *pca*).
  * `--reverse`           start at the *other* end of the selected axis.

Typical calls
~~~~~~~~~~~~~
    # All variables, start at min‑X end, save in plots/
    python stl_dat_surface_plot.py ice.stl results.dat \
           --all --axis x --save-dir plots

    # Single variable, start at max along PCA direction
    python stl_dat_surface_plot.py ice.stl results.dat \
           --var-index 2 --reverse

Key options (unchanged)
~~~~~~~~~~~~~~~~~~~~~~~
* `--all`          plot **every** extra variable beyond X,Y,Z.
* `--var-index`    plot only the given variable (integer).
* `--save-dir`     target folder for PNGs (auto‑created).
* `--dpi`          image resolution (default 300).

Dependencies
~~~~~~~~~~~~
    numpy ≥ 2.0, scipy, matplotlib, trimesh, scikit‑learn
Install with
`pip install numpy scipy matplotlib trimesh scikit-learn`.
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import trimesh
from scipy.spatial import cKDTree
from sklearn.decomposition import PCA

# --------------------------------------------------------------------------- #
# Tecplot *.dat* utilities
# --------------------------------------------------------------------------- #
TEC_VARIABLE_RE = re.compile(r'VARIABLES\s*=\s*(.*)', re.IGNORECASE)
TEC_ZONE_RE = re.compile(r'ZONE[^\n]*N\s*=\s*(\d+)[^\n]*', re.IGNORECASE)
FORTRAN_BARE_EXP_RE = re.compile(r'^([+-]?\d*\.?\d*)([+-]\d+)$')


def _split_quoted_list(s: str):
    parts, current, in_quotes = [], [], False
    for ch in s:
        if ch == '"':
            in_quotes = not in_quotes
            continue
        if ch == ',' and not in_quotes:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append(''.join(current).strip())
    return parts


def _to_float(tok: str) -> float:
    tok = tok.strip().replace('D', 'E').replace('d', 'E')
    if 'E' in tok or 'e' in tok:
        return float(tok)
    m = FORTRAN_BARE_EXP_RE.match(tok)
    if m:
        mant, exp = m.groups()
        return float(f"{mant}E{exp}")
    return float(tok)


def read_first_zone_dat(path: Path):
    coords, variables = [], []
    var_names = None
    text = path.read_text(encoding='utf‑8', errors='ignore')
    m = TEC_VARIABLE_RE.search(text)
    if m:
        var_names = _split_quoted_list(m.group(1))
    zone_m = TEC_ZONE_RE.search(text)
    if not zone_m:
        raise ValueError('No ZONE header found.')
    n_nodes = int(zone_m.group(1))
    lines = text[zone_m.end():].lstrip().splitlines()[:n_nodes]
    for ln in lines:
        nums = [_to_float(t) for t in re.split(r'[\s,]+', ln.strip()) if t]
        coords.append(nums[:3])
        variables.append(nums[3:])
    return np.array(coords), np.array(variables), var_names

# --------------------------------------------------------------------------- #
# STL path utilities
# --------------------------------------------------------------------------- #

def make_path_from_vertices(verts: np.ndarray, axis: str = 'pca', reverse: bool = False):
    """Return cumulative arc‑length *s* for each vertex.

    Parameters
    ----------
    axis : 'pca' | 'x' | 'y' | 'z'
        Direction used for ordering vertices.
    reverse : bool
        If *True*, start at the opposite end.
    """
    verts_u, inv = np.unique(verts, axis=0, return_inverse=True)

    if axis == 'pca':
        t = PCA(1).fit_transform(verts_u).ravel()
    else:
        idx = {'x': 0, 'y': 1, 'z': 2}[axis]
        t = verts_u[:, idx]

    order = np.argsort(t)
    if reverse:
        order = order[::-1]

    ordered = verts_u[order]
    seg_lens = np.linalg.norm(np.diff(ordered, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg_lens)])
    if np.ptp(ordered) > 10.0:  # assume mm → m
        s *= 1e-3
    return s, order, inv


def load_stl_vertices(path: Path):
    mesh = trimesh.load_mesh(str(path))
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError('STL contains multiple solids.')
    return mesh.vertices

# --------------------------------------------------------------------------- #
# Plot util
# --------------------------------------------------------------------------- #

def _safe_name(name: str):
    return re.sub(r'[^0-9A-Za-z._-]+', '_', name)

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main(argv=None):
    p = argparse.ArgumentParser(description='Plot Tecplot variables along STL‑surface s.')
    p.add_argument('stl', type=Path)
    p.add_argument('dat', type=Path)
    p.add_argument('--var-index', type=int, default=0,
                   help='Single variable index (0‑based, extras only)')
    p.add_argument('--all', action='store_true', help='Plot all extra variables')
    p.add_argument('--axis', choices=['pca', 'x', 'y', 'z'], default='pca',
                   help='Axis/direction for parametrisation (default: pca)')
    p.add_argument('--reverse', action='store_true',
                   help='Start at the opposite end')
    p.add_argument('--save-dir', type=Path, default=Path('.'),
                   help='Directory to save PNGs (created if missing)')
    p.add_argument('--dpi', type=int, default=300)
    args = p.parse_args(argv)

    verts = load_stl_vertices(args.stl)
    s_verts, order, inv = make_path_from_vertices(verts, args.axis, args.reverse)

    coords, vars_, names = read_first_zone_dat(args.dat)
    if vars_.size == 0:
        sys.exit('No variables beyond X,Y,Z found.')

    indices = range(vars_.shape[1]) if args.all else [args.var_index]
    if max(indices) >= vars_.shape[1]:
        sys.exit('var-index out of range.')

    tree = cKDTree(verts)
    _, nearest = tree.query(coords)
    s_nodes = s_verts[inv[nearest]]

    args.save_dir.mkdir(parents=True, exist_ok=True)

    for idx in indices:
        y = vars_[:, idx]
        seq = np.argsort(s_nodes)
        s_sorted, y_sorted = s_nodes[seq], y[seq]

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(s_sorted, y_sorted)
        ax.set_xlabel('s  [m]')
        label = (names[3+idx] if names and len(names) > 3+idx else f'Var{idx}')
        ax.set_ylabel(label)
        ax.grid(True)
        fig.tight_layout()

        fname = args.save_dir / f"{args.dat.stem}_{_safe_name(label)}.png"
        fig.savefig(fname, dpi=args.dpi)
        print(f'Saved {fname}')
        plt.close(fig)

    if not args.all:
        print('Finished single‑variable plot.')

if __name__ == '__main__':
    main()
