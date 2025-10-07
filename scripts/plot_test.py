#!/usr/bin/env python3
from __future__ import annotations
import argparse, re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import tri as mtri, colors

# ================= Style =================
def safe_style():
    import matplotlib as mpl
    mpl.rcParams["text.usetex"] = False
    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["font.serif"] = ["DejaVu Serif"]
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42
    mpl.rcParams["path.simplify"] = False

# =============== YAML ====================
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
    if not times:
        raise ValueError("CASE_MULTISHOT not found or empty in case.yaml")
    return times

# ======== Variable name normalization ========
_ID6 = re.compile(r"\.\d{6}\b", re.I)
def norm_keys(raw: str) -> List[str]:
    s = _ID6.sub("", raw).strip().lower()
    s = s.replace("pressure coefficient", "cp")
    s = re.sub(r"[^a-z0-9:]+", "", s)
    keys = {s, s.replace(":", "")}
    if ":" in s:
        keys.add(s.split(":", 1)[1])  # Suffix nach ':'
    return list(keys)

CP_KEYS = {"cp","c_p","pressurecoefficient","pressure_coefficient","cp:"}

# ============= Tecplot reader (FELINESEG) =============
def _parse_variables(lines: List[str]) -> Tuple[List[str], int]:
    i = next(k for k, ln in enumerate(lines) if "VARIABLES" in ln.upper())
    buf = lines[i]; j = i+1
    while j < len(lines) and not lines[j].lstrip().upper().startswith("ZONE"):
        buf += " " + lines[j]; j += 1
    names = re.findall(r'"([^"]+)"', buf)
    if not names: raise ValueError("No variable names in VARIABLES")
    return names, j

def read_first_zone_with_conn(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    var_names, after_vars = _parse_variables(lines)
    nvars = len(var_names)

    # map: mehrere Schlüssel pro Variable
    var_map: Dict[str,int] = {}
    for i, nm in enumerate(var_names):
        for k in norm_keys(nm):
            var_map[k] = i

    # locate ZONE header bounds
    z0 = next(i for i in range(after_vars, len(lines)) if lines[i].lstrip().upper().startswith("ZONE"))
    z1 = next((i for i in range(z0+1, len(lines)) if lines[i].lstrip().upper().startswith("ZONE")), len(lines))

    # merge header
    header = lines[z0]; k = z0+1
    while k < z1:
        s = lines[k].strip()
        if not s or s[0].isdigit() or s[0] in "+-.":
            break
        header += " " + s; k += 1

    mN = re.search(r"\bN\s*=\s*(\d+)", header, re.I)
    mE = re.search(r"\bE\s*=\s*(\d+)", header, re.I)
    ztype = (re.search(r"ZONETYPE\s*=\s*([A-Za-z0-9_]+)", header, re.I).group(1).upper()
             if re.search(r"ZONETYPE\s*=\s*([A-Za-z0-9_]+)", header, re.I) else "")
    if not mN: raise RuntimeError("ZONE header without N=")
    N = int(mN.group(1)); E = int(mE.group(1)) if mE else 0

    # read node table
    floats = []
    while k < z1 and len(floats) < N*nvars:
        s = lines[k].strip(); k += 1
        if not s: continue
        s = re.sub(r"(?<=\d)([+\-]\d{2,})", r"e\1", s)  # fix '1-03' → '1e-03'
        for t in s.replace(",", " ").split():
            if len(floats) >= N*nvars: break
            try: floats.append(float(t))
            except: pass
    if len(floats) < N*nvars:
        raise RuntimeError(f"Node data too short: {len(floats)} < {N*nvars}")
    nodes = np.array(floats, float).reshape(N, nvars)

    # read FELINESEG connectivity
    conn = np.empty((0,2), int)
    if ztype == "FELINESEG" and E > 0:
        edges = []; count = 0
        while k < z1 and count < E:
            parts = lines[k].strip().replace(",", " ").split(); k += 1
            ints = [int(p) for p in parts if re.fullmatch(r"[+\-]?\d+", p)]
            for a,b in zip(ints[::2], ints[1::2]):
                a -= 1; b -= 1
                if 0 <= a < N and 0 <= b < N and a != b:
                    edges.append([a,b]); count += 1
        if edges: conn = np.array(edges, int)

    return nodes, conn, var_names, var_map

def load_shot(root: Path, idx: int):
    p = root / f"{idx:06d}" / "merged.dat"
    txt = p.read_text(errors="ignore")
    if "VARIABLES" not in txt: raise RuntimeError(f"{p} has no VARIABLES header")
    return read_first_zone_with_conn(p)

# =========== s-Parametrisierung via Konnektivität ===========
def shoelace_area(x: np.ndarray, y: np.ndarray) -> float:
    xs = np.r_[x, x[0]]; ys = np.r_[y, y[0]]
    return 0.5 * np.sum(xs[:-1]*ys[1:] - xs[1:]*ys[:-1])

def build_adj(N: int, conn: np.ndarray) -> List[List[int]]:
    adj = [[] for _ in range(N)]
    for a,b in np.asarray(conn, int):
        if 0 <= a < N and 0 <= b < N and a != b:
            adj[a].append(b); adj[b].append(a)
    return adj

def walk_chain_from(start: int, adj: List[List[int]], x: np.ndarray, y: np.ndarray) -> np.ndarray:
    N = len(x)
    visited = np.zeros(N, bool)
    order = [start]; visited[start] = True
    prev = -1; cur = start
    for _ in range(N-1):
        nbrs = [nb for nb in adj[cur] if not visited[nb]]
        if not nbrs: break
        if len(nbrs) == 1 or prev == -1:
            nxt = nbrs[0]
        else:
            t_prev = np.array([x[cur]-x[prev], y[cur]-y[prev]])
            t_prev /= (np.linalg.norm(t_prev) + 1e-16)
            best, best_cos = None, -2.0
            for nb in nbrs:
                v = np.array([x[nb]-x[cur], y[nb]-y[cur]])
                c = (v @ t_prev) / (np.linalg.norm(v) + 1e-16)
                if c > best_cos: best_cos, best = c, nb
            nxt = best if best is not None else nbrs[0]
        order.append(nxt); visited[nxt] = True; prev, cur = cur, nxt

    # falls Inseln übrig: nearest-neighbour anhängen
    if len(order) < N:
        rem = np.where(~visited)[0].tolist()
        cur = order[-1]
        while rem:
            d2 = [( (x[i]-x[cur])**2 + (y[i]-y[cur])**2, i ) for i in rem]
            _, nxt = min(d2); order.append(nxt); visited[nxt] = True
            rem.remove(nxt); cur = nxt
    return np.array(order, int)

def order_along_connectivity(x: np.ndarray, y: np.ndarray, conn: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    N = len(x)
    if conn is None or conn.size == 0:
        # fallback: sortiere nach Winkel
        cx, cy = np.mean(x), np.mean(y)
        ang = np.arctan2(y-cy, x-cx)
        order = np.argsort(ang)
    else:
        adj = build_adj(N, conn)
        start = int(np.nanargmax(x))
        order = walk_chain_from(start, adj, x, y)
    xo, yo = x[order], y[order]

    # CCW erzwingen
    if np.isfinite(shoelace_area(xo, yo)) and shoelace_area(xo, yo) < 0:
        xo, yo = xo[::-1], yo[::-1]; order = order[::-1]

    # Start zurück auf TE (x=max)
    idx_te = int(np.argmax(xo))
    def rot(a): return np.concatenate([a[idx_te:], a[:idx_te]])
    xo, yo = rot(xo), rot(yo)
    order = np.r_[order[idx_te:], order[:idx_te]]
    return order, xo, yo

def s_from_xy(xo: np.ndarray, yo: np.ndarray) -> np.ndarray:
    ds = np.hypot(np.diff(xo), np.diff(yo))
    s = np.r_[0.0, np.cumsum(ds)]
    L = float(s[-1]) if s[-1] > 0 else 1.0
    return -1.0 + 2.0*(s / L)  # [-1,1]

# =============== Field access =================
def get_series(nodes: np.ndarray, var_map: Dict[str,int], key: str) -> np.ndarray:
    # exakte / alternative Schlüssel
    for k in norm_keys(key):
        if k in var_map: return nodes[:, var_map[k]].astype(float)
    # CP-Synonyme
    kcp = [k for k in CP_KEYS if k in var_map]
    if kcp: return nodes[:, var_map[kcp[0]]].astype(float)
    raise KeyError(f"Variable not found: {key}")

# =============== Collect (per field) ===============
def collect_curves(root: Path, field_key: str) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    shots = sorted([p for p in root.iterdir() if p.is_dir() and re.fullmatch(r"\d{6}", p.name)])
    if not shots: raise RuntimeError(f"No shot folders in {root}")
    SS, VS = [], []
    for sdir in shots:
        nodes, conn, var_names, var_map = load_shot(root, int(sdir.name))
        x = get_series(nodes, var_map, "x"); y = get_series(nodes, var_map, "y")
        order, xo, yo = order_along_connectivity(x, y, conn)
        s11 = s_from_xy(xo, yo)
        v = get_series(nodes, var_map, field_key)[order]
        SS.append(s11); VS.append(v)
    return SS, VS

# =============== Robust spacetime plot ===============
def find_extrema_indices(y: np.ndarray, min_separation: int = 3) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(y, float)
    dy = np.diff(y)
    is_max = (dy[:-1] > 0) & (dy[1:] < 0)
    is_min = (dy[:-1] < 0) & (dy[1:] > 0)
    idx_max = np.where(is_max)[0] + 1
    idx_min = np.where(is_min)[0] + 1
    def thin(idx):
        if len(idx) == 0: return idx
        keep = [idx[0]]
        for k in idx[1:]:
            if k - keep[-1] >= min_separation:
                keep.append(k)
        return np.array(keep, int)
    return thin(idx_max), thin(idx_min)

def plot_spacetime_field(outdir: Path, times: List[float],
                         ss: List[np.ndarray], vals: List[np.ndarray],
                         label: str, stem: str,
                         cmap: str = "RdBu_r",
                         levels: int = 100,
                         center_zero: bool = True,
                         mark_extrema: bool = False,
                         min_sep_extrema: int = 4):
    t_end = np.cumsum(times)
    if len(t_end) != len(ss): t_end = t_end[:len(ss)]

    S = np.concatenate(ss)
    T = np.concatenate([np.full_like(s, t, float) for s, t in zip(ss, t_end)])
    V = np.concatenate(vals)

    finite = np.isfinite(S) & np.isfinite(T) & np.isfinite(V)
    S, T, V = S[finite], T[finite], V[finite]
    if S.size == 0: raise RuntimeError("No finite data for spacetime plot.")

    # de-duplicate (S,T)
    st = np.round(np.column_stack([S, T]), 12)
    uniq, inv = np.unique(st, axis=0, return_inverse=True)
    if uniq.shape[0] < st.shape[0]:
        V_acc = np.zeros(uniq.shape[0]); cnt = np.zeros(uniq.shape[0])
        np.add.at(V_acc, inv, V); np.add.at(cnt, inv, 1.0)
        V = V_acc / np.maximum(cnt, 1.0)
        S, T = uniq[:,0], uniq[:,1]

    tri = mtri.Triangulation(S, T)
    if tri.triangles.size == 0:
        raise RuntimeError("Triangulation failed (too few unique points).")
    bad = np.any(~np.isfinite(V)[tri.triangles], axis=1)
    if np.any(bad): tri.set_mask(bad)

    norm = None
    if center_zero:
        vabs = float(np.nanmax(np.abs(V))) if V.size else 1.0
        norm = colors.TwoSlopeNorm(vcenter=0.0, vmin=-vabs, vmax=vabs)

    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    cs = ax.tricontourf(tri, V, levels=levels, cmap=cmap, norm=norm)
    fig.colorbar(cs, ax=ax, label=label)
    ax.set_xlabel("s/S (-)"); ax.set_ylabel("Time (s)"); ax.set_title(label)

    if mark_extrema:
        S_max, T_max, S_min, T_min = [], [], [], []
        for s_arr, v_arr, t in zip(ss, vals, t_end):
            m = np.isfinite(s_arr) & np.isfinite(v_arr)
            if not np.any(m): continue
            imax, imin = find_extrema_indices(v_arr[m], min_separation=min_sep_extrema)
            sshot = s_arr[m]
            if imax.size: S_max.extend(sshot[imax]); T_max.extend([t]*len(imax))
            if imin.size: S_min.extend(sshot[imin]); T_min.extend([t]*len(imin))
        if S_max: ax.scatter(S_max, T_max, s=10, c="#d62728", marker="^", edgecolors="k", linewidths=0.25, label="Maxima")
        if S_min: ax.scatter(S_min, T_min, s=10, c="#1f77b4", marker="v", edgecolors="k", linewidths=0.25, label="Minima")
        if S_max or S_min: ax.legend(loc="upper right", fontsize=8, frameon=True)

    fig.tight_layout()
    fig.savefig(outdir / f"{stem}_spacetime.pdf", dpi=300)
    plt.close(fig)

# =============== 3D Cp time-slices ===============
def plot_cp_3d_lines(outdir: Path, times: List[float],
                     xs_or_s: List[np.ndarray], cps: List[np.ndarray], xlabel: str):
    from mpl_toolkits.mplot3d import Axes3D  # noqa
    t_end = np.cumsum(times)
    if len(t_end) != len(xs_or_s): t_end = t_end[:len(xs_or_s)]
    fig = plt.figure(figsize=(7.2, 4.6))
    ax = fig.add_subplot(111, projection='3d')
    for t, x1d, cp in zip(t_end, xs_or_s, cps):
        ax.plot(x1d, np.full_like(x1d, t), cp, lw=1.0)
    ax.set_xlabel(xlabel); ax.set_ylabel("Time (s)"); ax.set_zlabel("Cp")
    ax.set_title("Cp evolution (time-sliced)")
    zlim = ax.get_zlim(); ax.set_zlim(zlim[::-1])  # invert Cp
    fig.tight_layout()
    fig.savefig(outdir / "cp_spacetime_3d.pdf", dpi=300)
    plt.close(fig)

# ================== Main ==================
def main():
    safe_style()
    ap = argparse.ArgumentParser(description="Multishot spacetime plots (s∈[-1,1]) with connectivity-based parametrization.")
    ap.add_argument("--root", type=Path, default=Path("analysis/MULTISHOT"))
    ap.add_argument("--case", type=Path, default=Path("case.yaml"))
    ap.add_argument("--out",  type=Path, default=Path("analysis/MULTISHOT/plots_important"))
    ap.add_argument("--field", type=str, default=None, help="Single field to plot (name in VARIABLES; shot-ID ignored).")
    ap.add_argument("--all", action="store_true", help="Plot spacetime for all fields (except x,y,z).")
    ap.add_argument("--cmap", type=str, default="RdBu_r")
    ap.add_argument("--levels", type=int, default=100)
    ap.add_argument("--center-zero", action="store_true", help="Center color scale at zero (good for Cp).")
    ap.add_argument("--mark-extrema", action="store_true")
    ap.add_argument("--cp-axis", choices=("xc","s"), default="xc", help="3D Cp lines over x/c or s/S.")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    times = read_case_multishot_times(args.case)

    # --- list variables once from first shot ---
    first = next(p for p in sorted(args.root.iterdir()) if p.is_dir() and re.fullmatch(r"\d{6}", p.name))
    nodes0, conn0, var_names0, var_map0 = load_shot(args.root, int(first.name))
    # build original-name → normalized map for nice labels
    pretty_names = {}
    for i, nm in enumerate(var_names0):
        for k in norm_keys(nm):
            pretty_names[k] = nm

    def plot_one(field_key: str):
        try:
            ss, vals = collect_curves(args.root, field_key)
            stem = re.sub(r"[^A-Za-z0-9]+", "_", field_key).strip("_").lower()
            label = pretty_names.get(next((k for k in norm_keys(field_key) if k in pretty_names), field_key), field_key)
            # center_zero nur für Cp sinnvoll
            c0 = args.center_zero or any(k in CP_KEYS for k in norm_keys(field_key))
            plot_spacetime_field(args.out, times, ss, vals, label, stem,
                                 cmap=args.cmap, levels=args.levels,
                                 center_zero=c0, mark_extrema=args.mark_extrema)
        except Exception as e:
            print(f"⚠️  Skip {field_key}: {e}")

    # --- single field or all fields ---
    if args.all:
        skip = {"x","y","z"}
        # alle unique normalisierten keys aus var_map0
        raw_keys = [k for k in var_map0.keys() if k not in skip]
        # nicht-doppelte Felder (ohne Suffix-only Duplikate)
        seen = set(); fields = []
        for k in raw_keys:
            base = k.replace(":", "")
            if base in seen: continue
            seen.add(base); fields.append(k)
        print(f"Plotting {len(fields)} fields...")
        for k in fields: plot_one(k)
    else:
        field = args.field or "cp"
        plot_one(field)

    # --- 3D Cp time-slices ---
    # s/S oder x/c
    if args.cp_axis == "s":
        ss, cps = collect_curves(args.root, "cp")
        plot_cp_3d_lines(args.out, times, ss, cps, xlabel="s/S")
    else:
        # x/c: nimm x aus nodes und skaliere mit chord; dazu denselben order verwenden
        shots = sorted([p for p in args.root.iterdir() if p.is_dir() and re.fullmatch(r"\d{6}", p.name)])
        XN, CPS = [], []
        for sdir in shots:
            nodes, conn, _, var_map = load_shot(args.root, int(sdir.name))
            x = get_series(nodes, var_map, "x"); y = get_series(nodes, var_map, "y")
            order, xo, yo = order_along_connectivity(x, y, conn)
            c = float(np.nanmax(xo)) if np.isfinite(xo).any() else 1.0
            xoc = xo / (c if c>0 else 1.0)
            cp = get_series(nodes, var_map, "cp")[order]
            XN.append(xoc); CPS.append(cp)
        plot_cp_3d_lines(args.out, times, XN, CPS, xlabel="x/c")

    print("✓ Done. Plots in:", args.out.resolve())

if __name__ == "__main__":
    main()
