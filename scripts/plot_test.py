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
from matplotlib import colors, tri as mtri
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def plot_spacetime_field(outdir: Path, times: list[float],
                         ss: list[np.ndarray], vals: list[np.ndarray],
                         label: str, stem: str,
                         cmap: str = "RdBu_r",
                         levels: int = 100,
                         center_zero: bool = True,
                         mark_extrema: bool = True,
                         min_sep_extrema: int = 4):
    """
    Robust tricontourf: filtert non-finite, maskiert Triangles mit non-finite Z.
    """
    # 1) Zeitachse
    t_end = np.cumsum(times)
    if len(t_end) != len(ss):
        t_end = t_end[:len(ss)]

    # 2) Flatten
    S = np.concatenate(ss)
    T = np.concatenate([np.full_like(s, t, dtype=float) for s, t in zip(ss, t_end)])
    V = np.concatenate(vals)

    # 3) Non-finite komplett entfernen (S,T,V gemeinsam)
    finite = np.isfinite(S) & np.isfinite(T) & np.isfinite(V)
    S, T, V = S[finite], T[finite], V[finite]

    # 4) Optional Duplikate (S,T) eindampfen (Mittelwert)
    if S.size == 0:
        raise RuntimeError("No finite data points for spacetime plot.")
    st = np.round(np.column_stack([S, T]), 12)  # numerische Stabilität
    uniq, inv = np.unique(st, axis=0, return_inverse=True)
    if uniq.shape[0] < st.shape[0]:
        V_acc = np.zeros(uniq.shape[0]); cnt = np.zeros(uniq.shape[0])
        np.add.at(V_acc, inv, V); np.add.at(cnt, inv, 1.0)
        V = V_acc / np.maximum(cnt, 1.0)
        S, T = uniq[:,0], uniq[:,1]

    # 5) Triangulation bauen + Triangles mit non-finite Z maskieren (sollte nach 3–4 nicht nötig sein, ist aber sicher)
    tri = mtri.Triangulation(S, T)
    if tri.triangles.size == 0:
        raise RuntimeError("Triangulation failed: not enough unique (s,t) points.")
    mask = np.any(~np.isfinite(V)[tri.triangles], axis=1)
    if mask.any():
        tri.set_mask(mask)

    # 6) Normierung (z.B. symmetrisch um 0 für Cp)
    if center_zero:
        vabs = np.nanmax(np.abs(V))
        norm = colors.TwoSlopeNorm(vcenter=0.0, vmin=-vabs, vmax=vabs)
    else:
        norm = None

    # 7) Plot
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    cs = ax.tricontourf(tri, V, levels=levels, cmap=cmap, norm=norm)
    cbar = fig.colorbar(cs, ax=ax, label=label)
    ax.set_xlabel("s/S (-)")  # du nutzt bereits [-1, 1]
    ax.set_ylabel("Time (s)")
    ax.set_title(label)

    # 8) Optional: Extrema markieren (nutzt deine find_extrema_indices-Funktion)
    if mark_extrema and 'find_extrema_indices' in globals():
        S_max, T_max, S_min, T_min = [], [], [], []
        for s_arr, v_arr, t in zip(ss, vals, t_end):
            if s_arr.size == 0 or v_arr.size == 0:
                continue
            # nur finite Punkte dieses Shots betrachten
            m = np.isfinite(s_arr) & np.isfinite(v_arr)
            if not np.any(m):
                continue
            imax, imin = find_extrema_indices(v_arr[m], min_separation=min_sep_extrema)
            sshot = s_arr[m]
            if imax.size:
                S_max.extend(sshot[imax]); T_max.extend([t]*len(imax))
            if imin.size:
                S_min.extend(sshot[imin]); T_min.extend([t]*len(imin))
        if S_max:
            ax.scatter(S_max, T_max, s=10, c="#d62728", marker="^",
                       linewidths=0.3, edgecolors="k", label="Maxima")
        if S_min:
            ax.scatter(S_min, T_min, s=10, c="#1f77b4", marker="v",
                       linewidths=0.3, edgecolors="k", label="Minima")
        if S_max or S_min:
            ax.legend(loc="upper right", fontsize=8, frameon=True)

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

def main():
    safe_style()
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("analysis/MULTISHOT"))
    ap.add_argument("--case", type=Path, default=Path("case.yaml"))
    ap.add_argument("--out", type=Path, default=Path("analysis/MULTISHOT/plots_important"))
    ap.add_argument("--cmap", type=str, default="RdBu_r")
    ap.add_argument("--levels", type=int, default=100)
    ap.add_argument("--center-zero", action="store_true", help="Center color scale at zero (for Cp etc.)")
    ap.add_argument("--mark-extrema", action="store_true")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    times = read_case_multishot_times(args.case)

    # Lade Header einmal aus dem ersten Shot
    first_shot = next(p for p in args.root.iterdir() if re.fullmatch(r"\d{6}", p.name))
    nodes, var_map = load_shot_nodes(args.root, int(first_shot.name))
    header_names = list(var_map.keys())

    print(f"Found {len(header_names)} variables.")
    skip_keys = {"x", "y", "z"}  # diese sind Koordinaten
    for key in header_names:
        if key in skip_keys:
            continue
        try:
            print(f"Plotting {key} ...")
            ss, vals = collect_curves(args.root, key, use_s_norm=True)
            stem = re.sub(r"[^A-Za-z0-9]+", "_", key).strip("_").lower()
            plot_spacetime_field(
                args.out,
                times,
                ss,
                vals,
                label=key,
                stem=stem,
                cmap=args.cmap,
                levels=args.levels,
                center_zero=args.center_zero,
                mark_extrema=args.mark_extrema,
            )
        except Exception as e:
            print(f"⚠️  Skipping {key}: {e}")
    print(f"✅ All plots saved in: {args.out.resolve()}")


if __name__ == "__main__":
    main()
