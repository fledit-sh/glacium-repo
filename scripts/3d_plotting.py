from __future__ import annotations
import argparse, re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt

# =========================
# CLI
# =========================
def parse_args():
    ap = argparse.ArgumentParser(description="Multishot overlays (no resampling).")
    ap.add_argument("--root", type=Path, default=Path("analysis/MULTISHOT"),
                    help="Folder with shot dirs 000001/.../merged.dat")
    ap.add_argument("--case", type=Path, default=Path("case.yaml"),
                    help="Path to case.yaml (reads CASE_MULTISHOT shot durations)")
    ap.add_argument("--out", type=Path, default=Path("analysis/MULTISHOT/plots_important"),
                    help="Output folder")
    ap.add_argument("--select", type=str, default="all",
                    help="Shot indices (0-based) like '0,1,3' or 'all' (default)")
    return ap.parse_args()

# =========================
# YAML (minimal) reader
# =========================
def read_case_multishot_times(case_yaml: Path) -> List[float]:
    if not case_yaml.exists():
        raise FileNotFoundError(f"{case_yaml} not found")
    lines = case_yaml.read_text(encoding="utf-8", errors="ignore").splitlines()
    times: List[float] = []
    in_block = False
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if not in_block:
            if re.match(r"^CASE_MULTISHOT\s*:", s):
                in_block = True
            continue
        m = re.match(r"^-\s*([0-9]+(?:\.[0-9]+)?)", s)
        if m:
            times.append(float(m.group(1)))
        else:
            if times:
                break
    if not times:
        raise ValueError("CASE_MULTISHOT not found or empty in case.yaml")
    return times

def six_digit(i: int) -> str:
    return f"{i:06d}"

# =========================
# Helpers (labels, geometry)
# =========================
def clean_label(name: str) -> str:
    s = name.strip()
    s = re.sub(r'^(?:droplet\.drop|swimsol\.ice)\.\d{6}:\s*', '', s, flags=re.I)
    return s or name

def rotate_start_argmax_x(*arrays):
    x = arrays[0]
    idx = int(np.nanargmax(x))
    def rot(a): return np.concatenate([a[idx:], a[:idx]])
    return tuple(rot(a) for a in arrays)

def enforce_clockwise(*arrays):
    # no-op for 1D chains; keep for compatibility
    return arrays

def arclength(x, y):
    dx = np.diff(x); dy = np.diff(y)
    return np.concatenate([[0.0], np.cumsum(np.sqrt(dx*dx + dy*dy))])

def scale_s_minus1_to_1(s):
    s0, s1 = float(s[0]), float(s[-1])
    if s1 == s0:
        return np.zeros_like(s)
    return -1.0 + 2.0*(s - s0)/(s1 - s0)

def safe_style():
    import matplotlib as mpl
    mpl.rcParams["text.usetex"] = False
    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["font.serif"] = ["DejaVu Serif"]
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42
    mpl.rcParams["path.simplify"] = False

# =========================
# Tecplot reader (with FELINESEG)
# =========================
def _read_first_zone_with_conn(path: Path):
    """
    Reads VARIABLES + ZONE N=...,E=..., ZONETYPE=FELINESEG + POINT data.
    Returns nodes (N, nvars), conn (E,2), var_names, var_map(normalized).
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # VARIABLES
    i_var = next((k for k, ln in enumerate(lines) if ln.lstrip().upper().startswith("VARIABLES")), None)
    if i_var is None:
        raise ValueError("VARIABLES not found")
    buf = lines[i_var]; j = i_var+1
    while j < len(lines) and not lines[j].lstrip().upper().startswith("ZONE"):
        buf += " " + lines[j]; j += 1
    var_names = re.findall(r'"([^"]+)"', buf)
    if not var_names:
        raise ValueError("No variable names parsed")
    var_map = { re.sub(r"[^A-Za-z0-9]","",n).lower(): k for k,n in enumerate(var_names) }

    # ZONE header
    z0 = next((i for i, ln in enumerate(lines) if ln.lstrip().upper().startswith("ZONE")), None)
    if z0 is None:
        raise ValueError("ZONE header not found")
    header = lines[z0]
    mN = re.search(r"\bN\s*=\s*(\d+)", header, flags=re.I)
    mE = re.search(r"\bE\s*=\s*(\d+)", header, flags=re.I)
    if not (mN and mE):
        raise ValueError("N= or E= missing in ZONE header")
    N = int(mN.group(1)); E = int(mE.group(1))

    # Node data
    vals = []
    k = z0+1
    float_needed = N * len(var_names)
    while k < len(lines) and len(vals) < float_needed:
        s = lines[k].strip(); k += 1
        if not s: continue
        if s.upper().startswith("ZONE"): break
        s = re.sub(r"(?<=\d)([+\-]\d{2,})", r"e\1", s)  # fix 1-03 -> 1e-03
        for t in s.replace(",", " ").split():
            try: vals.append(float(t))
            except: pass
    nodes = np.array(vals[:float_needed], dtype=float).reshape(N, len(var_names))

    # Connectivity lines (pairs, 1-based)
    edges = []
    while k < len(lines) and len(edges) < E:
        s = lines[k].strip(); k += 1
        if not s: continue
        parts = s.replace(",", " ").split()
        ints = []
        for p in parts:
            try: ints.append(int(p))
            except: pass
        for a, b in zip(ints[::2], ints[1::2]):
            edges.append((a-1, b-1))
    conn = np.array(edges, dtype=int).reshape(-1, 2)
    return nodes, conn, var_names, var_map

def order_from_connectivity(N: int, conn: np.ndarray) -> np.ndarray:
    """Build path along the FELINESEG polyline from connectivity graph."""
    if conn.size == 0:
        return np.arange(N, dtype=int)
    deg = np.zeros(N, dtype=int)
    for a,b in conn:
        if 0 <= a < N and 0 <= b < N:
            deg[a] += 1; deg[b] += 1
    adj = [[] for _ in range(N)]
    for a,b in conn:
        if 0 <= a < N and 0 <= b < N:
            adj[a].append(b); adj[b].append(a)
    starts = [i for i,d in enumerate(deg) if d == 1]
    start = starts[0] if starts else 0
    visited = np.zeros(N, dtype=bool)
    order = np.empty(N, dtype=int)
    order[0] = start; visited[start] = True
    curr = start
    for i in range(1, N):
        nxts = [nb for nb in adj[curr] if not visited[nb]]
        if not nxts:
            nxt = int(np.argmax(~visited))
        else:
            nxt = nxts[0]
        order[i] = nxt
        visited[nxt] = True
        curr = nxt
    return order

# =========================
# Fallback reader (no header)
# =========================
# Heuristik für dein Testprojekt (Spaltennummern):
FALLBACK_COLS = {
    "x": 0,            # X
    "y": 1,            # Y
    "tau1": 16,        # shear component 1
    "tau2": 17,        # shear component 2
    "tau3": 18,        # shear component 3 (oft 0)
    "q_classic": 19,   # heat flux
    "q_gresho": 20,    # alternative heat flux
    "beta": 27,        # collection efficiency
    "freezing_frac": 31,
    "h_ice_a": 32,     # ice thickness (m)
}

def robust_load_nodes_fallback(path: Path) -> np.ndarray:
    """Liest gemischte Datei, filtert Node-Zeilen (viele Spalten), gibt 2D float-Array zurück."""
    rows = []
    with open(path, "r", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if not s: continue
            if s.upper().startswith(("TITLE","VARIABLES","ZONE")):  # sichere Seite
                continue
            parts = s.replace(",", " ").split()
            vals = []
            ok = True
            for p in parts:
                try:
                    vals.append(float(p) if p.lower()!="nan" else np.nan)
                except:
                    ok = False; break
            if ok and vals:
                rows.append(vals)
    if not rows:
        raise ValueError(f"No numeric rows found in {path}")
    width = max(len(r) for r in rows)
    arr = np.full((len(rows), width), np.nan)
    for i, r in enumerate(rows):
        arr[i,:len(r)] = r
    # Node-Zeilen: viele gültige Spalten (Konnekivitätszeilen haben nur 2 Integers)
    finite_counts = np.sum(np.isfinite(arr), axis=1)
    node_mask = finite_counts >= (0.8 * np.nanmax(finite_counts))  # robust
    return arr[node_mask,:]

# =========================
# Variable selection
# =========================
VAR_KEYS = {
    "x": "x",
    "y": "y",
    "cp": "cp",
    "tau1": "sf1shearstresspa",
    "tau2": "sf2shearstresspa",
    "tau3": "sf3shearstresspa",
    "q_classic": "classicalheatfluxwm2",
    "q_gresho": "greshoheatfluxwm2",
    "beta": "dropletdrop000002collectionefficiencydroplet",
    "freezing_frac": "swimsolice000002freezingfraction",
    "h_ice_a": "swimsolice000002icethicknessm",
    "q_conv": "swimsolice000002currentconvectiveheatflux",
    "q_evap": "swimsolice000002evaporativeheatflux",
}

def pick_var(var_map: Dict[str,int], key: str) -> Optional[int]:
    target = VAR_KEYS.get(key)
    if target is None:
        return None
    for norm, idx in var_map.items():
        if norm == target:
            return idx
    if key == "h_ice_a":
        for norm, idx in var_map.items():
            if norm.startswith("swimsolice000002icethicknessm"):
                return idx
    return None

def try_variable_series_by_index(nodes_o: np.ndarray, key: str) -> Tuple[str, np.ndarray]:
    idx = FALLBACK_COLS.get(key)
    if idx is None or idx >= nodes_o.shape[1]:
        raise KeyError(f"fallback column for {key} not available")
    label = key
    data = nodes_o[:, idx].astype(float)
    return label, data

def variable_series(nodes_o: np.ndarray, var_names: List[str] | None,
                    var_map: Dict[str,int] | None, key: str) -> Tuple[str, np.ndarray]:
    if var_map:
        idx = pick_var(var_map, key)
        if idx is not None:
            label = clean_label(var_names[idx]) if var_names else key
            return label, nodes_o[:, idx].astype(float)
    # Fallback by column index
    return try_variable_series_by_index(nodes_o, key)

# =========================
# Per-shot loading & ordering
# =========================
def load_shot(root: Path, shot_idx: int) -> Tuple[np.ndarray, np.ndarray, List[str] | None, Dict[str,int] | None]:
    path = root / f"{six_digit(shot_idx)}" / "merged.dat"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}")
    text_head = path.read_text(errors="ignore")[:256].upper()
    if "VARIABLES" in text_head and "ZONE" in text_head:
        nodes, conn, var_names, var_map = _read_first_zone_with_conn(path)
    else:
        nodes = robust_load_nodes_fallback(path)
        conn = np.empty((0,2), dtype=int)
        var_names = None
        var_map = None
    return nodes, conn, var_names, var_map

def prep_xy_s(nodes: np.ndarray, conn: np.ndarray, var_map: Dict[str,int] | None) -> Tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
    # Geometry indices
    if var_map:
        xi = var_map.get("x")
        yi = var_map.get("y", None)
    else:
        xi = FALLBACK_COLS.get("x")
        yi = FALLBACK_COLS.get("y")
    x = nodes[:, xi].astype(float)
    y = nodes[:, yi].astype(float) if yi is not None else np.zeros_like(x)

    # Order along wall
    N = nodes.shape[0]
    order = order_from_connectivity(N, conn)
    nodes_o = nodes[order, :]
    x_o = x[order]; y_o = y[order]
    arrays = (x_o, y_o, nodes_o)
    arrays = rotate_start_argmax_x(*arrays)
    arrays = enforce_clockwise(*arrays)
    arrays = rotate_start_argmax_x(*arrays)
    x_o, y_o, nodes_o = arrays

    # Normalize by chord
    c = float(np.nanmax(x_o))
    if not np.isfinite(c) or c == 0.0:
        raise RuntimeError("Invalid chord length (max X = 0)")
    x_over_c = x_o / c
    y_over_c = y_o / c
    s_vals = arclength(x_o, y_o)
    s_unit = scale_s_minus1_to_1(s_vals)
    return nodes_o, x_over_c, y_over_c, s_unit, order

# =========================
# Plotting
# =========================
def ensure_outdir(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    return base

def overlay_var_over_xc(ax, root: Path, sel: List[int], cum_times: List[float],
                        key: str, ylabel: str, title: Optional[str]=None):
    for k0 in sel:
        k = k0 + 1  # convert 0-based to shot folder index
        try:
            nodes, conn, var_names, var_map = load_shot(root, k)
            nodes_o, x_over_c, y_over_c, s_unit, order = prep_xy_s(nodes, conn, var_map)
            if key == "tau_abs":
                _, t1 = variable_series(nodes_o, var_names, var_map, "tau1")
                _, t2 = variable_series(nodes_o, var_names, var_map, "tau2")
                # tau3 optional
                try:
                    _, t3 = variable_series(nodes_o, var_names, var_map, "tau3")
                except KeyError:
                    t3 = np.zeros_like(t1)
                arr = np.sqrt(t1**2 + t2**2 + t3**2)
            else:
                _, arr = variable_series(nodes_o, var_names, var_map, key)
            lbl = f"t={cum_times[k0]:.0f} s"
            ax.plot(x_over_c, arr, lw=1.0, label=lbl)
        except Exception as e:
            print(f"[warn] shot {k:06d}: {e}")
            continue
    ax.set_xlabel("x/c"); ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.legend(title="Shot end time", fontsize=8, ncols=2, handlelength=1.8)
def plot_ice_spacetime(root: Path, times: list[float], outdir: Path):
    """3D surface or contour plot h_ice(x/c, t)."""
    shots = []
    for i in range(len(times)):
        try:
            nodes, conn, var_names, var_map = load_shot(root, i+1)
            nodes_o, x_over_c, y_over_c, s_unit, order = prep_xy_s(nodes, conn, var_map)
            _, h = variable_series(nodes_o, var_names, var_map, "h_ice_a")
            shots.append((x_over_c, h))
        except Exception as e:
            print(f"[warn] {i+1:06d}: {e}")
            continue

    # Einheitliches Gitter für X
    x_common = np.linspace(0, 1.0, 300)
    t_common = np.cumsum(times)
    H = np.zeros((len(t_common), len(x_common)))

    for j, (x, h) in enumerate(shots):
        H[j, :] = np.interp(x_common, x, h, left=np.nan, right=np.nan)

    # 3D surface (optional)
    from mpl_toolkits.mplot3d import Axes3D  # noqa
    fig = plt.figure(figsize=(7, 4.5))
    ax = fig.add_subplot(111, projection='3d')
    X, T = np.meshgrid(x_common, t_common)
    ax.plot_surface(X, T, H, cmap="viridis", rstride=1, cstride=1, linewidth=0)
    ax.set_xlabel("x/c")
    ax.set_ylabel("Time (s)")
    ax.set_zlabel("Ice thickness (m)")
    ax.set_title("Ice accretion evolution")
    fig.tight_layout()
    fig.savefig(outdir / "h_ice_spacetime_surface.pdf")
    plt.close(fig)

    # 2D contour
    fig, ax = plt.subplots(figsize=(6.3, 3.8))
    c = ax.contourf(x_common, t_common, H, levels=50, cmap="viridis")
    fig.colorbar(c, ax=ax, label="h_ice (m)")
    ax.set_xlabel("x/c")
    ax.set_ylabel("Time (s)")
    ax.set_title("Ice thickness evolution over time")
    fig.tight_layout()
    fig.savefig(outdir / "h_ice_spacetime_contour.pdf")
    plt.close(fig)
# =========================
# Main
# =========================
def main():
    args = parse_args()
    safe_style()
    outdir = ensure_outdir(args.out)

    # Times & selection
    times = read_case_multishot_times(args.case)
    nshots = len(times)
    cum_times = list(np.cumsum(times))

    if args.select.strip().lower() == "all":
        sel = list(range(nshots))
    else:
        sel = []
        for s in args.select.split(","):
            s = s.strip()
            if not s: continue
            i = int(s)
            if i < 0: i = nshots + i
            if 0 <= i < nshots: sel.append(i)
        sel = sorted(set(sel))
        if not sel:
            sel = list(range(nshots))  # fallback to all

    root = args.root

    # 1) h_ice overlays (all selected)
    fig, ax = plt.subplots(figsize=(6.3, 4.0))
    overlay_var_over_xc(ax, root, sel, cum_times, "h_ice_a", "Ice thickness h_ice (m)", "Ice accretion over shots")
    fig.tight_layout(); fig.savefig(outdir / "h_ice_vs_xc_overlay_full.pdf"); plt.close(fig)

    # 2) Drivers (all selected as Wunsch)
    for key, ylabel, fname in [
        ("tau_abs", r"|tau_w| (Pa)", "tauw_vs_xc_overlay_full.pdf"),
        ("q_classic", "Heat flux (W/m^2)", "qflux_vs_xc_overlay_full.pdf"),
        ("beta", "Collection efficiency (-)", "beta_vs_xc_overlay_full.pdf"),
        ("freezing_frac", "Freezing fraction (-)", "freezing_vs_xc_overlay_full.pdf"),
    ]:
        fig, ax = plt.subplots(figsize=(6.3, 4.0))
        overlay_var_over_xc(ax, root, sel, cum_times, key, ylabel)
        fig.tight_layout(); fig.savefig(outdir / fname); plt.close(fig)
    # Nach den Overlays:
    plot_ice_spacetime(root, times, outdir)

    print("Wrote overlays to:", outdir.resolve())

if __name__ == "__main__":
    main()
