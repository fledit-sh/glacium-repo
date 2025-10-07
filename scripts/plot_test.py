#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, re, json
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import tri as mtri, colors

# =============== Style ===============
def safe_style():
    import matplotlib as mpl
    mpl.rcParams["text.usetex"] = False
    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["font.serif"] = ["DejaVu Serif"]
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42
    mpl.rcParams["path.simplify"] = False

# =============== YAML ===============
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
    if not times: raise ValueError("CASE_MULTISHOT not found or empty in case.yaml")
    return times

# ===== Name-Normalisierung (Shot-ID-agnostisch) =====
_ID6 = re.compile(r"\.\d{6}\b", re.I)
def norm_keys(raw: str) -> List[str]:
    s = _ID6.sub("", raw).strip().lower()
    s = s.replace("pressure coefficient", "cp")
    s = re.sub(r"[^a-z0-9:]+", "", s)
    keys = {s, s.replace(":", "")}
    if ":" in s:
        keys.add(s.split(":", 1)[1])
    return list(keys)

CP_KEYS = {"cp","c_p","pressurecoefficient","pressure_coefficient","cp:"}

# =============== Tecplot Reader (FELINESEG) ===============
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

    var_map: Dict[str,int] = {}
    for i, nm in enumerate(var_names):
        for k in norm_keys(nm):
            var_map[k] = i

    z0 = next(i for i in range(after_vars, len(lines)) if lines[i].lstrip().upper().startswith("ZONE"))
    z1 = next((i for i in range(z0+1, len(lines)) if lines[i].lstrip().upper().startswith("ZONE")), len(lines))

    header = lines[z0]; k = z0+1
    while k < z1:
        s = lines[k].strip()
        if not s or s[0].isdigit() or s[0] in "+-.": break
        header += " " + s; k += 1

    mN = re.search(r"\bN\s*=\s*(\d+)", header, re.I)
    mE = re.search(r"\bE\s*=\s*(\d+)", header, re.I)
    ztype = (re.search(r"ZONETYPE\s*=\s*([A-Za-z0-9_]+)", header, re.I).group(1).upper()
             if re.search(r"ZONETYPE\s*=\s*([A-Za-z0-9_]+)", header, re.I) else "")
    if not mN: raise RuntimeError("ZONE header without N=")
    N = int(mN.group(1)); E = int(mE.group(1)) if mE else 0

    floats = []
    while k < z1 and len(floats) < N*nvars:
        s = lines[k].strip(); k += 1
        if not s: continue
        s = re.sub(r"(?<=\d)([+\-]\d{2,})", r"e\1", s)
        for t in s.replace(",", " ").split():
            if len(floats) >= N*nvars: break
            try: floats.append(float(t))
            except: pass
    if len(floats) < N*nvars:
        raise RuntimeError(f"Node data too short: {len(floats)} < {N*nvars}")
    nodes = np.array(floats, float).reshape(N, nvars)

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

# =============== s-Parametrisierung (Konnektivität) ===============
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
                cosang = (v @ t_prev) / (np.linalg.norm(v) + 1e-16)
                if cosang > best_cos: best_cos, best = cosang, nb
            nxt = best if best is not None else nbrs[0]
        order.append(nxt); visited[nxt] = True; prev, cur = cur, nxt

    if len(order) < N:
        rem = np.where(~visited)[0].tolist()
        cur = order[-1]
        while rem:
            d2 = [((x[i]-x[cur])**2 + (y[i]-y[cur])**2, i) for i in rem]
            _, nxt = min(d2); order.append(nxt); visited[nxt] = True
            rem.remove(nxt); cur = nxt
    return np.array(order, int)

def order_along_connectivity(x: np.ndarray, y: np.ndarray, conn: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    N = len(x)
    if conn is None or conn.size == 0:
        cx, cy = np.mean(x), np.mean(y)
        ang = np.arctan2(y-cy, x-cx)
        order = np.argsort(ang)
    else:
        adj = build_adj(N, conn)
        start = int(np.nanargmax(x))
        order = walk_chain_from(start, adj, x, y)

    xo, yo = x[order], y[order]
    A = shoelace_area(xo, yo)
    if np.isfinite(A) and A < 0:
        xo, yo = xo[::-1], yo[::-1]
        order = order[::-1]

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

# =============== Field access ===============
def get_series(nodes: np.ndarray, var_map: Dict[str,int], key: str) -> np.ndarray:
    for k in norm_keys(key):
        if k in var_map: return nodes[:, var_map[k]].astype(float)
    kcp = [k for k in CP_KEYS if k in var_map]
    if kcp: return nodes[:, var_map[kcp[0]]].astype(float)
    raise KeyError(f"Variable not found: {key}")

# =============== Collect (per field) ===============
def collect_curves(root: Path, field_key: str) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    shots = sorted([p for p in root.iterdir() if p.is_dir() and re.fullmatch(r"\d{6}", p.name)])
    if not shots: raise RuntimeError(f"No shot folders in {root}")
    SS, VS = [], []
    for sdir in shots:
        nodes, conn, _, var_map = load_shot(root, int(sdir.name))
        x = get_series(nodes, var_map, "x"); y = get_series(nodes, var_map, "y")
        order, xo, yo = order_along_connectivity(x, y, conn)
        s11 = s_from_xy(xo, yo)
        v = get_series(nodes, var_map, field_key)[order]
        SS.append(s11); VS.append(v)
    return SS, VS

# =============== Extrema (optional) ===============
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

# =============== Auto policies (NaN & Color) ===============
def classify_field(label: str) -> str:
    """'signed' (z.B. Cp), 'frac01' (0..1), 'nonneg' (>=0), 'generic'."""
    l = label.lower()
    if any(k in l for k in ["freezing", "fraction"]): return "frac01"
    if any(k in l for k in ["collection efficiency", "beta"]): return "frac01"
    if any(k in l for k in ["film", "thickness", "mass caught", "ice thickness"]): return "nonneg"
    if any(k in l for k in ["heat", "flux", "temperature"]): return "nonneg"
    if "cp" in l or "pressure" in l: return "signed"
    return "generic"

def choose_cmap_and_norm(policy: str, V: np.ndarray, center_zero_flag: bool):
    if policy == "signed" or center_zero_flag:
        vabs = float(np.nanmax(np.abs(V))) if V.size else 1.0
        return "RdBu_r", colors.TwoSlopeNorm(vcenter=0.0, vmin=-vabs, vmax=vabs)
    if policy == "frac01":
        vmax = float(np.nanmax(V)) if V.size else 1.0
        vmax = 1.0 if vmax <= 0 else min(1.0, vmax)
        return "viridis", colors.Normalize(vmin=0.0, vmax=vmax)
    if policy == "nonneg":
        vmax = float(np.nanmax(V)) if V.size else 1.0
        return "inferno", colors.Normalize(vmin=0.0, vmax=vmax if vmax>0 else 1.0)
    return "cividis", None

# =============== Robust spacetime plot ===============
def plot_spacetime_field(outdir: Path, times: List[float],
                         ss: List[np.ndarray], vals: List[np.ndarray],
                         label: str, stem: str,
                         cmap: str | None = None,
                         levels: int = 120,
                         center_zero: bool = False,
                         mark_extrema: bool = False,
                         min_sep_extrema: int = 4,
                         nan_policy: str = "auto"):
    t_end = np.cumsum(times)
    if len(t_end) != len(ss): t_end = t_end[:len(ss)]

    S = np.concatenate(ss)
    T = np.concatenate([np.full_like(s, t, float) for s, t in zip(ss, t_end)])
    V = np.concatenate(vals)

    # NaN-Handling (auto)
    field_class = classify_field(label) if nan_policy == "auto" else ""
    if nan_policy == "zero" or field_class in {"frac01", "nonneg"}:
        mask = np.isfinite(S) & np.isfinite(T)
        S, T, V = S[mask], T[mask], V[mask]
        V = np.where(np.isfinite(V), V, 0.0)
    else:
        finite = np.isfinite(S) & np.isfinite(T) & np.isfinite(V)
        S, T, V = S[finite], T[finite], V[finite]
    if S.size == 0: raise RuntimeError("No finite data for spacetime plot.")

    # de-duplicate (S,T) by averaging V
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

    # Auto colormap / normalization (unless user provided cmap)
    auto_cmap, auto_norm = choose_cmap_and_norm(field_class, V, center_zero)
    if cmap is None: cmap = auto_cmap
    norm = auto_norm if center_zero or field_class in {"signed", "frac01", "nonneg"} else None

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
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
    zlim = ax.get_zlim(); ax.set_zlim(zlim[::-1])
    fig.tight_layout()
    fig.savefig(outdir / "cp_spacetime_3d.pdf", dpi=300)
    plt.close(fig)

# =============== HDF5 Cache ===============
import h5py

def save_preprocessed_dataset(outpath: Path, case_yaml: Path, root: Path):
    times = read_case_multishot_times(case_yaml)
    shots = sorted([p for p in root.iterdir() if p.is_dir() and re.fullmatch(r"\d{6}", p.name)])
    if not shots: raise RuntimeError(f"No shot folders in {root}")

    with h5py.File(outpath, "w") as h5:
        h5.attrs["source"] = str(root)
        h5.attrs["num_shots"] = len(shots)
        h5.attrs["case_times"] = json.dumps(times)

        for sdir, t in zip(shots, np.cumsum(times)):
            grp = h5.create_group(sdir.name)
            nodes, conn, var_names, vmap = load_shot(root, int(sdir.name))
            x = get_series(nodes, vmap, "x"); y = get_series(nodes, vmap, "y")
            order, xo, yo = order_along_connectivity(x, y, conn)
            s_norm = s_from_xy(xo, yo)

            grp.create_dataset("x", data=xo, compression="gzip", compression_opts=6)
            grp.create_dataset("y", data=yo, compression="gzip", compression_opts=6)
            grp.create_dataset("s_norm", data=s_norm, compression="gzip", compression_opts=6)
            grp.attrs["time"] = float(t)
            grp.attrs["num_nodes"] = int(len(xo))

            for key, idx in vmap.items():
                try:
                    data = nodes[:, idx][order]
                    grp.create_dataset(key, data=data, compression="gzip", compression_opts=6)
                except Exception:
                    pass

def load_preprocessed_dataset(h5path: Path) -> Tuple[List[str], List[str], List[float]]:
    with h5py.File(h5path, "r") as h5:
        times = json.loads(h5.attrs["case_times"])
        shots = sorted(h5.keys())
        keys = set()
        for sid in shots:
            keys.update(h5[sid].keys())
        return shots, sorted(keys), times

# =============== Main ===============
def main():
    # --- Defaults (einfach anpassen, wenn nötig) ---
    root     = Path("analysis/MULTISHOT")
    casefile = Path("case.yaml")
    outdir   = Path("analysis/MULTISHOT/plots_important")
    dataset  = Path("dataset.h5")

    # Plot-Defaults
    plot_all_fields = True       # alle Felder statt nur "Cp"
    cmap_override   = None       # None = Auto je Feld (Cp: RdBu_r, Fraktionen: viridis, etc.)
    levels          = 120        # feinere Konturlinien
    center_zero     = False      # Cp wird trotzdem automatisch symmetrisch zentriert
    mark_extrema    = True      # bei Bedarf True
    nan_policy      = "auto"     # "auto" (empfohlen), "drop" oder "zero"
    cp_axis         = "s"       # "xc" oder "s"

    # --- Setup ---
    safe_style()
    outdir.mkdir(parents=True, exist_ok=True)

    # Cache bauen, falls nicht vorhanden
    if not dataset.exists():
        print(f"📦 Erzeuge Cache: {dataset}")
        save_preprocessed_dataset(dataset, casefile, root)
    else:
        print(f"📂 Verwende Cache: {dataset}")

    # Metadaten laden
    shots, all_keys, times = load_preprocessed_dataset(dataset)

    # Hilfsfunktion: ein Feld aus dem Cache plotten
    def plot_field(field_key: str):
        ss, vals = [], []
        with h5py.File(dataset, "r") as h5f:
            for sid in shots:
                grp = h5f[sid]
                if field_key not in grp:
                    continue
                ss.append(grp["s_norm"][:])      # s ∈ [-1,1], CCW, via Konnektivität
                vals.append(grp[field_key][:])
        if not ss:
            print(f"⚠️  Feld nicht gefunden: {field_key}")
            return
        stem = re.sub(r"[^A-Za-z0-9]+", "_", field_key).strip("_").lower()
        label = field_key
        plot_spacetime_field(
            outdir, times, ss, vals, label, stem,
            cmap=cmap_override,
            levels=levels,
            center_zero=center_zero,
            mark_extrema=mark_extrema,
            nan_policy=nan_policy
        )

    # Alle Felder (außer x,y,z,s_norm) plotten
    skip = {"x","y","z","s_norm"}
    if plot_all_fields:
        fields = [k for k in all_keys if k not in skip]
        print(f"🖼️  Plotte {len(fields)} Felder …")
        for k in fields:
            plot_field(k)
    else:
        plot_field("cp")

    # 3D-Cp-Plot (Zeit-Slices)
    with h5py.File(dataset, "r") as h5f:
        ss_list, cps_list, xcs_list = [], [], []
        for sid in shots:
            grp = h5f[sid]
            if "cp" in grp:
                ss_list.append(grp["s_norm"][:])
                cps_list.append(grp["cp"][:])
                x = grp["x"][:]
                c = float(np.nanmax(x)) if np.isfinite(x).any() else 1.0
                xcs_list.append(x / (c if c>0 else 1.0))
    if cp_axis == "s":
        plot_cp_3d_lines(outdir, times, ss_list, cps_list, xlabel="s/S")
    else:
        plot_cp_3d_lines(outdir, times, xcs_list, cps_list, xlabel="x/c")

    print(f"✅ Fertig. Plots in: {outdir.resolve()}")


if __name__ == "__main__":
    main()
