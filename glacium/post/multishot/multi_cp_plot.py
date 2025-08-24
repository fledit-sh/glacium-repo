#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
try:
    import scienceplots  # type: ignore
    plt.style.use(["science","no-latex"])
except Exception:
    pass
# --- multi-size saving ---
SIZES = [("full", (6.3, 3.9)), ("dbl", (3.15, 2.0))]

def save_in_sizes(fig, base: Path, stem: str, dpi=300):
    """Save *the same* figure in multiple sizes by resizing before each save."""
    for label, size in SIZES:
        fig.set_size_inches(*size, forward=True)
        fig.tight_layout()
        for ext in ("png","pdf","svg"):
            fig.savefig(base / f"{stem}_{label}.{ext}", dpi=dpi)

_num_line_re = re.compile(r'^[\s\+\-]?(?:\d|\.)')

def _normalize(name: str) -> str:
    name = name.strip()
    name = re.split(r"[\s(;:]", name, 1)[0]
    name = re.sub(r"[^A-Za-z0-9]", "", name)
    return name.lower()

def _parse_variables(lines):
    i = next((k for k, ln in enumerate(lines) if ln.lstrip().upper().startswith("VARIABLES")), None)
    if i is None:
        raise ValueError("VARIABLES line not found")
    buf = lines[i]
    j = i + 1
    while j < len(lines) and not lines[j].lstrip().upper().startswith("ZONE"):
        buf += " " + lines[j]
        j += 1
    names = re.findall(r'"([^"]+)"', buf)
    if not names:
        raise ValueError("No variable names parsed from VARIABLES")
    return names, { _normalize(v): k for k, v in enumerate(names) }, j

def read_first_zone_with_conn(path: Path):
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    var_names, var_map, after_vars = _parse_variables(lines)
    nvars = len(var_names)

    z0 = next((i for i in range(after_vars, len(lines)) if lines[i].lstrip().upper().startswith("ZONE")), None)
    if z0 is None:
        raise ValueError("No ZONE header found")
    z1 = next((i for i in range(z0+1, len(lines)) if lines[i].lstrip().upper().startswith("ZONE")), len(lines))

    header_ext = lines[z0]
    k = z0 + 1
    while k < z1:
        s = lines[k].strip()
        if _num_line_re.match(s) or s.startswith('"'):
            break
        header_ext += " " + s
        k += 1

    mN = re.search(r"\bN\s*=\s*(\d+)", header_ext, flags=re.I)
    mE = re.search(r"\bE\s*=\s*(\d+)", header_ext, flags=re.I)
    ztype = (re.search(r"ZONETYPE\s*=\s*([A-Za-z0-9_]+)", header_ext, flags=re.I).group(1).upper()
             if re.search(r"ZONETYPE\s*=\s*([A-Za-z0-9_]+)", header_ext, flags=re.I) else "")
    if not mN:
        raise ValueError("N= not found in first ZONE header")
    N = int(mN.group(1)); E = int(mE.group(1)) if mE else 0

    floats = []
    while k < z1 and len(floats) < N*nvars:
        s = lines[k].strip(); k += 1
        if not s: continue
        s = re.sub(r"(?<=\d)([+\-]\d{2,})", r"e\1", s)
        for t in s.split():
            if len(floats) >= N*nvars: break
            try: floats.append(float(t))
            except ValueError: pass
    if len(floats) < N*nvars:
        raise ValueError(f"Node data too short: {len(floats)} < {N*nvars}")
    nodes = np.array(floats[:N*nvars], dtype=float).reshape(N, nvars)

    conn = np.empty((0,2), dtype=int)
    if ztype.upper() == "FELINESEG" and E > 0:
        edges = []; count = 0
        while k < z1 and count < E:
            toks = lines[k].strip().split(); k += 1
            if len(toks) == 2 and all(re.fullmatch(r"[+\-]?\d+", t) for t in toks):
                a = int(toks[0]) - 1; b = int(toks[1]) - 1
                if 0 <= a < N and 0 <= b < N:
                    edges.append([a, b]); count += 1
        if edges: conn = np.array(edges, dtype=int)

    return nodes, conn, var_names, var_map

def order_from_connectivity(N: int, conn: np.ndarray) -> np.ndarray:
    if conn is None or conn.size == 0:
        return np.arange(N, dtype=int)
    from collections import defaultdict
    adj = defaultdict(list)
    for a,b in conn:
        a = int(a); b = int(b)
        adj[a].append(b); adj[b].append(a)

    used = set(); start = next(iter(adj)); path = [start]; cur = start
    steps = 0; max_steps = max(4*len(conn), 10)
    while steps < max_steps:
        steps += 1; nxt = None
        for nb in adj[cur]:
            e = tuple(sorted((cur, nb)))
            if e not in used: used.add(e); nxt = nb; break
        if nxt is None: break
        path.append(nxt); cur = nxt
    if len(path) < N:
        seen = set(path); path.extend(i for i in range(N) if i not in seen)
    return np.array(path, dtype=int)

def rotate_start_argmax_x(*arrays):
    x = arrays[0]; idx = int(np.nanargmax(x))
    def rot(a): return np.concatenate([a[idx:], a[:idx]])
    return tuple(rot(a) for a in arrays)

def enforce_clockwise(*arrays):
    x, y = arrays[0], arrays[1]
    if x.size >= 3:
        xs = np.concatenate([x, x[:1]]); ys = np.concatenate([y, y[:1]])
        area = 0.5 * np.sum(xs[:-1]*ys[1:] - xs[1:]*ys[:-1])
        if area > 0: return tuple(a[::-1] for a in arrays)
    return arrays

def arclength(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    dx = np.diff(x); dy = np.diff(y)
    return np.concatenate([[0.0], np.cumsum(np.sqrt(dx*dx + dy*dy))])

def s_normalized_minus1_to_1(s: np.ndarray) -> np.ndarray:
    s0, s1 = float(s[0]), float(s[-1])
    if not (np.isfinite(s0) and np.isfinite(s1)) or s1 == s0: return np.zeros_like(s)
    return -1.0 + 2.0*(s - s0)/(s1 - s0)

def plot_cp_set(base: Path, curves, x_label: str, suffix: str):
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    if len(curves) >= 3:
        for name, xp, cp in curves[1:-1]:
            ax.plot(xp, cp, color='0.6', linewidth=0.4, linestyle='solid')
    name0, x0, cp0 = curves[0]; ax.plot(x0, cp0, color='k', linewidth=0.8, linestyle='solid')
    nameL, xL, cpL = curves[-1]; ax.plot(xL, cpL, color='r', linewidth=0.8, linestyle='solid')
    ax.invert_yaxis(); ax.set_xlabel(x_label); ax.set_ylabel("Cp");
    from matplotlib.lines import Line2D
    proxies = [Line2D([0],[0], color='k', lw=0.8, label=f"Clean"),
               Line2D([0],[0], color='r', lw=0.8, label=f"Iced"),
               Line2D([0],[0], color='0.6', lw=0.4, label="Evolution")]
    ax.legend(handles=proxies, loc="best")
    save_in_sizes(fig, base, f"cp_all_{suffix}", dpi=300)
    plt.close(fig)

def plot_xy(base: Path, curves_xy, xlim=(-0.2, 0.1)):
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    if len(curves_xy) >= 3:
        for name, xc, yc in curves_xy[1:-1]:
            ax.plot(xc, yc, color='0.6', linewidth=0.4)
    name0, x0, y0 = curves_xy[0]; ax.plot(x0, y0, color='k', linewidth=0.8)
    nameL, xL, yL = curves_xy[-1]; ax.plot(xL, yL, color='r', linewidth=0.8)
    ax.set_xlabel("x/c");
    ax.set_ylabel("y/c");
    ax.set_aspect("equal", adjustable="box");
    from matplotlib.lines import Line2D
    proxies = [Line2D([0],[0], color='k', lw=0.8, label=f"Clean"),
               Line2D([0],[0], color='r', lw=0.8, label=f"Iced"),
               Line2D([0],[0], color='0.6', lw=0.4, label="Evolution")]
    ax.set_xlim(xlim)
    ax.legend(handles=proxies, loc="best")

    save_in_sizes(fig, base, "curve_all_xy", dpi=300)
    plt.close(fig)


def plot_sy(base: Path, curves_sy):
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    if len(curves_sy) >= 3:
        for name, sN, yc in curves_sy[1:-1]:
            ax.plot(sN, yc, color='0.6', linewidth=0.4)
    name0, s0, y0 = curves_sy[0]; ax.plot(s0, y0, color='k', linewidth=0.8)
    nameL, sL, yL = curves_sy[-1]; ax.plot(sL, yL, color='r', linewidth=0.8)

    ax.set_xlabel("s/S")
    ax.set_ylabel("y/c")
    # ax.set_aspect("equal", adjustable="box")   # <<< hinzugefügt
    ax.set_xlim([-0.5,0.5])
    from matplotlib.lines import Line2D
    proxies = [Line2D([0],[0], color='k', lw=0.8, label="Clean"),
               Line2D([0],[0], color='r', lw=0.8, label="Iced"),
               Line2D([0],[0], color='0.6', lw=0.4, label="Evolution")]
    ax.legend(handles=proxies, loc="best")

    save_in_sizes(fig, base, "curve_all_sy", dpi=300)
    plt.close(fig)


def plot_h(base: Path, shot_ids, h_values):
    pairs = sorted(zip(shot_ids, h_values), key=lambda t: int(re.sub(r'^0+', '', t[0]) or '0'))
    xs = np.arange(len(pairs)); labels = [p[0] for p in pairs]; hs = np.array([p[1] for p in pairs], float)
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    ax.plot(xs, hs, marker='+', linestyle='--', color='0.6', linewidth=0.8, markersize=3.5, mec = 'k', mfc = 'k')
    ax.set_xlabel("Shot"); ax.set_ylabel("h = S / (N-1)"); ax.grid(True, linestyle=':', alpha=0.4)
    if len(xs) > 12:
        step = max(1, len(xs)//12); xticks = xs[::step];
        xticklabels = [int(labels[i]) for i in xticks]
    else:
        xticks = xs; xticklabels = labels
    ax.set_xticks(xticks); ax.set_xticklabels(xticklabels, rotation=45, ha='right')
    ax.minorticks_off()  # no minor ticks on x/y
    save_in_sizes(fig, base, "h_over_shots", dpi=300)
    plt.close(fig)

def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Create Cp plots across multiple shots")
    ap.add_argument(
        "base",
        type=Path,
        nargs="?",
        default=Path("."),
        help="Directory containing shot folders (default: current directory)",
    )
    args = ap.parse_args(argv)
    base = args.base
    shots = sorted([p for p in base.iterdir() if p.is_dir() and re.fullmatch(r"\d{6}", p.name)])
    if not shots:
        print("No six-digit shot directories in", base); return

    curves_xc, curves_s, curves_xy, curves_sy = [], [], [], []
    shot_ids, h_values = [], []

    for shot in shots:
        merged = shot / "merged.dat"
        if not merged.exists():
            print(f"[skip] {shot.name}: merged.dat not found"); continue
        try:
            nodes, conn, var_names, var_map = read_first_zone_with_conn(merged)
            ix = var_map.get("x"); iy = var_map.get("y")
            icp = (var_map.get("cp") or var_map.get("c_p") or var_map.get("pressurecoefficient") or var_map.get("pressure_coefficient"))
            if ix is None or icp is None:
                print(f"[skip] {shot.name}: x or Cp not found"); continue
            order = order_from_connectivity(nodes.shape[0], conn)
            x = nodes[order, ix].astype(float)
            y = nodes[order, iy].astype(float) if iy is not None else np.zeros_like(x)
            cp = nodes[order, icp].astype(float)
            x, y, cp = rotate_start_argmax_x(x, y, cp)
            x, y, cp = enforce_clockwise(x, y, cp)

            xmax = float(np.nanmax(x))
            if not np.isfinite(xmax) or xmax <= 0:
                print(f"[skip] {shot.name}: invalid max(x)"); continue
            xc = x / xmax; yc = y / xmax

            s = arclength(x, y); s_unit = s_normalized_minus1_to_1(s)

            curves_xc.append((shot.name, xc, cp))
            curves_s.append((shot.name, s_unit, cp))
            curves_xy.append((shot.name, xc, yc))

            # s-normalized vs y/c for contour over arclength
            curves_sy.append((shot.name, s_unit, yc))

            N_nodes = x.size
            h = float(s[-1]) / max(N_nodes - 1, 1)
            shot_ids.append(shot.name); h_values.append(h)
        except Exception as e:
            print(f"[skip] {shot.name}: {e}")

    if not curves_xc:
        print("No curves to plot."); return

    plot_cp_set(base, curves_xc, "x/c", "xc")
    plot_cp_set(base, curves_s,  "s",   "s")
    plot_xy(base, curves_xy)
    plot_sy(base, curves_sy)
    plot_h(base, shot_ids, h_values)

    pairs = sorted(zip(shot_ids, h_values), key=lambda t: int(re.sub(r'^0+', '', t[0]) or '0'))
    with open(base / "h_over_shots_simple.csv", "w") as f:
        f.write("shot,h\n")
        for shot, h in pairs:
            f.write(f"{shot},{h:.10g}\n")
    print("Saved all plots and h_over_shots_simple.csv in", base)

if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
