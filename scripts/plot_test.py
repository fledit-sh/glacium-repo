#!/usr/bin/env python3
from __future__ import annotations
import argparse, re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

# ============== Style =================
def safe_style():
    import matplotlib as mpl
    mpl.rcParams["text.usetex"] = False
    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["font.serif"] = ["DejaVu Serif"]
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42
    mpl.rcParams["path.simplify"] = False

# ============== YAML ==================
def read_case_multishot_times(case_yaml: Path) -> List[float]:
    lines = case_yaml.read_text(encoding="utf-8", errors="ignore").splitlines()
    times: List[float] = []
    in_block = False
    for ln in lines:
        s = ln.strip()
        if not s: continue
        if not in_block:
            if re.match(r"^CASE_MULTISHOT\s*:", s): in_block = True
            continue
        m = re.match(r"^-\s*([0-9]+(?:\.[0-9]+)?)", s)
        if m: times.append(float(m.group(1)))
        elif times: break
    if not times: raise ValueError("CASE_MULTISHOT not found in case.yaml")
    return times

# ======== Name-Normalisierung =========
_ID6 = re.compile(r"\.\d{6}\b", re.I)
CP_KEYS = {"cp","c_p","pressurecoefficient","pressure_coefficient"}

def norm_all_keys(raw: str) -> List[str]:
    s = _ID6.sub("", raw).strip().lower()
    s = s.replace("pressure coefficient", "cp")
    s = re.sub(r"[^a-z0-9:]+", "", s)
    keys = {s}
    if ":" in s: keys.add(s.split(":", 1)[1])    # Suffix nach ':'
    keys.add(s.replace(":", ""))
    return list(keys)

# ======== Geometrie & Orientierung =====
def rotate_by_index(idx: int, *arrays):
    def rot(a): return np.concatenate([a[idx:], a[:idx]])
    return tuple(rot(a) for a in arrays)

def idx_te_max_x(x: np.ndarray) -> int:
    # TE = größtes x; bei Ties nimm ersten
    return int(np.nanargmax(x))

def poly_signed_area(x: np.ndarray, y: np.ndarray) -> float:
    # Shoelace; >0 => CCW
    xs = np.r_[x, x[0]]; ys = np.r_[y, y[0]]
    return 0.5 * np.sum(xs[:-1]*ys[1:] - xs[1:]*ys[:-1])

def ensure_ccw_sync(x: np.ndarray, y: np.ndarray, *others):
    A = poly_signed_area(x, y)
    if np.isfinite(A) and A < 0.0:
        x, y = x[::-1], y[::-1]
        others = tuple(a[::-1] for a in others)
    return (x, y, *others)

def arclength(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    dx, dy = np.diff(x), np.diff(y)
    return np.r_[0.0, np.cumsum(np.hypot(dx, dy))]

def s_norm01(s: np.ndarray) -> np.ndarray:
    L = float(s[-1] - s[0])
    return (s - s[0]) / L if L != 0.0 else np.zeros_like(s)

# ============== Tecplot Reader =========
def _parse_variables(lines: List[str]):
    i = next(k for k, ln in enumerate(lines) if "VARIABLES" in ln.upper())
    buf = lines[i]; j = i + 1
    while j < len(lines) and not lines[j].lstrip().upper().startswith("ZONE"):
        buf += " " + lines[j]; j += 1
    names = re.findall(r'"([^"]+)"', buf)
    return names, j

def read_first_zone(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    names, after = _parse_variables(lines)
    var_map: Dict[str,int] = {}
    for i, n in enumerate(names):
        for key in norm_all_keys(n):
            var_map[key] = i
    z0 = next(i for i in range(after, len(lines)) if lines[i].lstrip().upper().startswith("ZONE"))
    header = lines[z0]
    mN = re.search(r"N\s*=\s*(\d+)", header)
    if not mN: raise RuntimeError("ZONE header without N=")
    N = int(mN.group(1))
    data = []
    for ln in lines[z0+1:]:
        if not ln or ln.upper().startswith("ZONE"): break
        for v in ln.replace(",", " ").split():
            try: data.append(float(v))
            except: pass
    arr = np.array(data[:N*len(names)], dtype=float).reshape(N, len(names))
    return arr, var_map

# ============== Loader =================
def load_shot_nodes(root: Path, idx: int):
    p = root / f"{idx:06d}" / "merged.dat"
    text = p.read_text(errors="ignore")
    if "VARIABLES" in text:
        return read_first_zone(p)
    raise RuntimeError(f"{p} has no header")

# ============== Series =================
def get_series(nodes: np.ndarray, var_map: Dict[str,int], key: str) -> np.ndarray:
    keys = norm_all_keys(key)
    for k in keys:
        if k in var_map: return nodes[:, var_map[k]]
    if key.strip().lower() in CP_KEYS:
        for ck in CP_KEYS:
            if ck in var_map: return nodes[:, var_map[ck]]
    raise KeyError(f"{key} not found; first keys={list(var_map.keys())[:12]}")

# ============== Collect (mit CCW-Garantie) =========
def collect_curves(root: Path, var: str, use_s_norm: bool) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    shots = sorted([p for p in root.iterdir() if p.is_dir() and re.fullmatch(r"\d{6}", p.name)])
    Xs, Vs = [], []
    for sdir in shots:
        nodes, var_map = load_shot_nodes(root, int(sdir.name))
        # Geometrie
        x = nodes[:, var_map["x"]].astype(float)
        y = nodes[:, var_map["y"]].astype(float)
        # EIN gemeinsamer Rotationsindex aus x:
        idx = idx_te_max_x(x)
        x, y = rotate_by_index(idx, x, y)
        # Feld laden und identisch rotieren:
        v = get_series(nodes, var_map, var).astype(float)
        (v,) = rotate_by_index(idx, v)
        # CCW erzwingen – und ALLE Arrays spiegeln, falls nötig:
        x, y, v = ensure_ccw_sync(x, y, v)
        # Abszisse
        if use_s_norm:
            s = arclength(x, y); absc = s_norm01(s)
        else:
            c = float(np.nanmax(x)); absc = (x / c) if c > 0 else x
        Xs.append(absc); Vs.append(v)
    return Xs, Vs

# ============== Plots ==================
def plot_spacetime_field(outdir, times, ss, vals, label, stem):
    t_end = np.cumsum(times)
    if len(t_end) != len(ss):
        t_end = t_end[:len(ss)]
    S = np.concatenate(ss)
    T = np.concatenate([np.full_like(s, t) for s, t in zip(ss, t_end)])
    V = np.concatenate(vals)

    # symmetrische Skalierung um den Mittelwert
    vmin, vmax = np.nanmin(V), np.nanmax(V)
    vabs = max(abs(vmin), abs(vmax))
    norm = colors.TwoSlopeNorm(vcenter=0.0, vmin=-vabs, vmax=vabs)

    fig, ax = plt.subplots(figsize=(6.5, 4))
    cs = ax.tricontourf(S, T, V, levels=100, cmap="RdBu_r", norm=norm)
    fig.colorbar(cs, ax=ax, label=label)
    ax.set_xlabel("s/S (-)")
    ax.set_ylabel("Time (s)")
    ax.set_title(label)
    fig.tight_layout()
    fig.savefig(outdir / f"{stem}_spacetime.pdf", dpi=300)
    plt.close(fig)

def plot_cp_3d(outdir: Path, times: List[float], xs: List[np.ndarray],
               cps: List[np.ndarray], xlabel: str):
    from mpl_toolkits.mplot3d import Axes3D  # noqa
    t_end = np.cumsum(times)
    fig = plt.figure(figsize=(7.0, 4.2))
    ax = fig.add_subplot(111, projection="3d")
    for s, x, cp in zip(t_end, xs, cps):
        ax.plot(x, np.full_like(x, s), cp, lw=1.0)
    ax.set_xlabel(xlabel); ax.set_ylabel("Time (s)"); ax.set_zlabel("Cp")
    ax.set_title("Cp evolution"); ax.invert_zaxis()
    fig.tight_layout(); fig.savefig(outdir / "cp_spacetime_3d.pdf"); plt.close(fig)

# ============== Main ===================
def main():
    safe_style()
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("analysis/MULTISHOT"))
    ap.add_argument("--case", type=Path, default=Path("case.yaml"))
    ap.add_argument("--field", type=str, default="swimsol.ice:Ice thickness (m)"),
    ap.add_argument("--cp-axis", choices=["xc","s"], default="xc")
    ap.add_argument("--out", type=Path, default=Path("analysis/MULTISHOT/plots_important"))
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    times = read_case_multishot_times(args.case)

    # 2D (s/S vs. t) – CCW
    ss, vals = collect_curves(args.root, args.field, use_s_norm=True)
    stem = re.sub(r"[^A-Za-z0-9]+", "_", args.field).strip("_").lower()
    plot_spacetime_field(args.out, times, ss, vals, args.field, stem)

    # 3D Cp-Zeit-Slices – CCW
    use_s = args.cp_axis == "s"
    xs, cps = collect_curves(args.root, "cp", use_s_norm=use_s)
    xlabel = "s/S" if use_s else "x/c"
    plot_cp_3d(args.out, times, xs, cps, xlabel)

    print("✓ Plots saved in:", args.out.resolve())

if __name__ == "__main__":
    main()
