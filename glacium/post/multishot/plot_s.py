from __future__ import annotations
import argparse, re, sys
from pathlib import Path
from typing import List, Tuple, Dict
import numpy as np
import matplotlib.pyplot as plt

# -------------------- Utilities --------------------
_num_line_re = re.compile(r'^[\s\+\-]?(?:\d|\.)')
# only these exact prefixes
PREFIX_RE = re.compile(r'^(?:droplet\.drop|swimsol\.ice)\.\d{6}:\s*', flags=re.I)

def _normalize(name: str) -> str:
    name = name.strip()
    name = re.split(r"[\s(;:]", name, 1)[0]
    name = re.sub(r"[^A-Za-z0-9]", "", name)
    return name.lower()

def clean_label(name: str) -> str:
    s = name.strip()
    s = PREFIX_RE.sub("", s)
    return s or name

def safe_name(name: str) -> str:
    # for filenames, also remove slashes/colons etc.
    s = clean_label(name)
    s = s.replace(":", "__")
    s = re.sub(r'[<>:"/\\|?*]', "_", s)
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "var"

# -------------------- Parsing merged.dat (first ZONE incl. connectivity) --------------------
def _parse_variables(lines: List[str]) -> Tuple[List[str], Dict[str,int]]:
    # VARIABLES can span multiple lines before first ZONE
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
    return names, { _normalize(v): k for k, v in enumerate(names) }

def _read_first_zone_with_conn(path: Path) -> Tuple[np.ndarray, np.ndarray, List[str], Dict[str,int]]:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()

    var_names, var_map = _parse_variables(lines)
    nvars = len(var_names)

    # find first ZONE header
    z0 = next((i for i, ln in enumerate(lines) if ln.lstrip().upper().startswith("ZONE")), None)
    if z0 is None:
        raise ValueError("No ZONE header found")
    # find end (next ZONE or EOF)
    z1 = next((i for i in range(z0+1, len(lines)) if lines[i].lstrip().upper().startswith("ZONE")), len(lines))

    # collect header continuation to get N, E, ZONETYPE
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

    # read node floats until N*nvars
    floats: List[float] = []
    while k < z1 and len(floats) < N*nvars:
        s = lines[k].strip()
        k += 1
        if not s:
            continue
        s = re.sub(r"(?<=\d)([+\-]\d{2,})", r"e\1", s)  # fix '1.23+05'
        for t in s.split():
            if len(floats) >= N*nvars:
                break
            try:
                floats.append(float(t))
            except ValueError:
                pass
    if len(floats) < N*nvars:
        raise ValueError(f"Node data too short: {len(floats)} < {N*nvars}")
    nodes = np.array(floats[:N*nvars], dtype=float).reshape(N, nvars)

    # read connectivity if FELINESEG and E>0: E lines with two ints
    conn = np.empty((0,2), dtype=int)
    if ztype == "FELINESEG" and E > 0:
        edges = []
        count = 0
        while k < z1 and count < E:
            toks = lines[k].strip().split()
            k += 1
            if len(toks) == 2 and all(re.fullmatch(r"[+\-]?\d+", t) for t in toks):
                a = int(toks[0]) - 1
                b = int(toks[1]) - 1
                if 0 <= a < N and 0 <= b < N:
                    edges.append([a, b])
                    count += 1
        if edges:
            conn = np.array(edges, dtype=int)

    return nodes, conn, var_names, var_map

# -------------------- Connectivity ordering --------------------
def order_from_connectivity(N: int, conn: np.ndarray) -> np.ndarray:
    """Return an ordered list of node indices following the polyline. Falls back to range(N) if no conn."""
    if conn is None or conn.size == 0:
        return np.arange(N, dtype=int)
    from collections import defaultdict
    adj = defaultdict(list)
    for a,b in conn:
        a = int(a); b = int(b)
        adj[a].append(b); adj[b].append(a)

    # choose a node in the largest connected component
    visited = set()
    best_component = []
    for start in adj.keys():
        if start in visited:
            continue
        # BFS to gather component
        comp = []
        stack = [start]
        visited.add(start)
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in adj[u]:
                if v not in visited:
                    visited.add(v); stack.append(v)
        if len(comp) > len(best_component):
            best_component = comp

    start = min(best_component) if best_component else 0
    order = [start]
    used_edges = set()
    cur = start
    steps = 0
    max_steps = max(4*len(conn), 10)
    while steps < max_steps:
        steps += 1
        nxt = None
        for nb in adj[cur]:
            e = tuple(sorted((cur, nb)))
            if e not in used_edges:
                used_edges.add(e)
                nxt = nb
                break
        if nxt is None:
            break
        order.append(nxt)
        cur = nxt

    # append any nodes not visited (stable index order)
    if len(order) < N:
        seen = set(order)
        order.extend([i for i in range(N) if i not in seen])
    return np.array(order, dtype=int)

# -------------------- Orientation & s helpers (apply to multiple arrays) --------------------
def rotate_start_argmax_x(*arrays):
    """Rotate all arrays consistently so that index of max(x) becomes 0. arrays[0]=x, arrays[1]=y, rest any."""
    x = arrays[0]
    idx = int(np.nanargmax(x))
    def rot(a): return np.concatenate([a[idx:], a[:idx]])
    return tuple(rot(a) for a in arrays)

def enforce_clockwise(*arrays):
    """Reverse all arrays if current order is counter-clockwise to enforce clockwise. arrays[0]=x, arrays[1]=y"""
    x, y = arrays[0], arrays[1]
    if x.size >= 3:
        xs = np.concatenate([x, x[:1]])
        ys = np.concatenate([y, y[:1]])
        area = 0.5 * np.sum(xs[:-1]*ys[1:] - xs[1:]*ys[:-1])
        if area > 0:  # CCW
            return tuple(a[::-1] for a in arrays)
    return arrays

def arclength(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    dx = np.diff(x); dy = np.diff(y)
    return np.concatenate([[0.0], np.cumsum(np.sqrt(dx*dx + dy*dy))])

def scale_s_minus1_to_1(s: np.ndarray) -> np.ndarray:
    # map start to -1, end to +1
    s0, s1 = float(s[0]), float(s[-1])
    if not (np.isfinite(s0) and np.isfinite(s1)) or s1 == s0:
        return np.zeros_like(s)
    return -1.0 + 2.0*(s - s0)/(s1 - s0)

# -------------------- Plotting helpers --------------------
from matplotlib.collections import LineCollection

def draw_bicolor(ax, x_plot, y_plot, x_for_dir, lw=1.2):
    # nur gültige Punkte
    m = np.isfinite(x_plot) & np.isfinite(y_plot) & np.isfinite(x_for_dir)
    if m.sum() < 2:
        return

    # Indizes kontinuierlicher Stücke (NaNs „überbrücken“ wir bewusst)
    idx = np.flatnonzero(m)
    # Segment-Endpunkte
    p0 = np.column_stack([x_plot[idx[:-1]], y_plot[idx[:-1]]])
    p1 = np.column_stack([x_plot[idx[1:]],  y_plot[idx[1:]]])

    # Farblogik je Segment
    dx_dir = x_for_dir[idx[1:]] - x_for_dir[idx[:-1]]
    colors = np.where(dx_dir < 0.0, "r", "k")

    # Segments als (N, 2, 2)
    segs = np.stack([p0, p1], axis=1)

    lc = LineCollection(
        segs,
        colors=colors,
        linewidths=lw,
        antialiased=False,          # verhindert Haarlinien
        capstyle="butt",
        joinstyle="miter",
        rasterized=False,           # wichtig: Vektor-Export
    )
    ax.add_collection(lc)

    # Datenbereich updaten + y autoskalieren (x-Limits setzt der Aufrufer)
    ax.update_datalim(segs.reshape(-1, 2))
    ax.autoscale_view(scalex=False, scaley=True)

def save_two_sizes(outdir: Path, stem: str, make_fig_fn):
    sizes = [("full", (6.3, 3.9)), ("dbl", (3.15, 2.0))]
    for tag, sz in sizes:
        fig, ax, suffix = make_fig_fn(sz, tag)
        fig.tight_layout()
        base = outdir / f"{stem}_{suffix}_{tag}"
        # PNG für schnelle Vorschau
        fig.savefig(base.with_suffix(".png"), dpi=200)
        # Vektorformate
        fig.savefig(base.with_suffix(".pdf"))
        fig.savefig(base.with_suffix(".svg"))
        plt.close(fig)

# -------------------- Main --------------------
# -------------------- Main --------------------
def main():
    from matplotlib.backends.backend_pdf import PdfPages

    ap = argparse.ArgumentParser(description="Plot ALL variables vs x/c (Y as y/c) and vs s ([-1,1]).")
    ap.add_argument("merged", type=Path, help="merged.dat (Tecplot ASCII)")
    ap.add_argument("maybe_output", nargs="?", default=None,
                    help="Optional legacy positional (e.g. .../curve_s.pdf) — its parent is used as outdir.")
    ap.add_argument("--outdir", type=Path, default=None)
    ap.add_argument("--style", type=str, default="science,ieee", help='Matplotlib styles (default). Use "" to disable.')
    args = ap.parse_args()

    # Determine outdir
    if args.maybe_output:
        outdir = Path(args.maybe_output).parent
    elif args.outdir is not None:
        outdir = args.outdir
    else:
        outdir = Path("plots_x_over_c")
    outdir.mkdir(parents=True, exist_ok=True)

    # Style without external LaTeX
    if args.style:
        try:
            import scienceplots  # noqa: F401
        except Exception:
            pass
        try:
            plt.style.use([s.strip() for s in args.style.split(",") if s.strip()])
        except Exception as e:
            print(f"[warn] Could not apply style: {e}")
    import matplotlib as mpl
    mpl.rcParams["text.usetex"] = False
    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["font.serif"] = ["DejaVu Serif"]
    mpl.rcParams["path.simplify"] = False
    mpl.rcParams["agg.path.chunksize"] = 0
    # Vektorfreundliche Fonts (echter Text in PDF)
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"]  = 42

    # Read merged (first zone + connectivity)
    nodes, conn, var_names, var_map = _read_first_zone_with_conn(args.merged)
    N = nodes.shape[0]
    order = order_from_connectivity(N, conn)

    # Geometry helpers
    x_idx = var_map.get("x"); y_idx = var_map.get("y")
    if x_idx is None:
        sys.exit("X not found in VARIABLES")
    x = nodes[:, x_idx].astype(float)
    y = nodes[:, y_idx].astype(float) if y_idx is not None else np.zeros_like(x)

    # Apply connectivity order to ALL variables
    nodes_o = nodes[order, :]
    x_o = x[order]; y_o = y[order]

    # Rotate to start at max(x), enforce clockwise, then rotate again to keep start at max(x) — for ALL arrays
    arrays = (x_o, y_o, nodes_o)
    arrays = rotate_start_argmax_x(*arrays)
    arrays = enforce_clockwise(*arrays)
    arrays = rotate_start_argmax_x(*arrays)
    x_o, y_o, nodes_o = arrays

    # Chord & normalized geometry
    c = float(np.nanmax(x_o))
    if not np.isfinite(c) or c == 0.0:
        sys.exit("max(X) invalid; cannot compute x/c")
    x_over_c = x_o / c
    y_over_c = y_o / c

    # s in [-1,1], with start at -1
    s_vals = arclength(x_o, y_o)
    s_unit = scale_s_minus1_to_1(s_vals)

    # X-axis padding (in x/c)
    xmin = float(np.nanmin(x_over_c)); xmax = float(np.nanmax(x_over_c))
    pad_lo = xmin - 0.05; pad_hi = xmax + 0.05
    if not np.isfinite(pad_lo): pad_lo = -0.05
    if not np.isfinite(pad_hi): pad_hi = 1.05
    if pad_lo >= pad_hi: pad_lo, pad_hi = xmin - 0.05, xmin + 0.05

    sizes = [("full", (6.3, 3.9)), ("dbl", (3.15, 2.0))]
    pdf_path = outdir / "all_plots.pdf"

    with PdfPages(pdf_path) as pdf:

        # 0) Geometry: y/c vs x/c mit equal aspect
        if y_idx is not None:
            for tag, sz in sizes:
                fig, ax = plt.subplots(figsize=sz)
                draw_bicolor(ax, x_over_c, y_over_c, x_over_c, lw=1.0)
                ax.set_xlim(pad_lo, pad_hi)
                ax.set_xlabel("x/c")
                ax.set_ylabel("y/c")
                ax.set_aspect("equal", adjustable="box")

                base = outdir / f"curve_geom_yc_vs_xc_{tag}"
                fig.tight_layout()
                fig.savefig(base.with_suffix(".pdf"))   # Einzel-PDF
                pdf.savefig(fig)                        # Multi-Page-PDF
                plt.close(fig)

        # 1) Alle Variablen vs x/c und vs s
        for i, vname in enumerate(var_names):
            if i == y_idx:
                continue
            vraw = nodes_o[:, i].astype(float)
            label = clean_label(vname)
            fname = safe_name(vname)

            # vs x/c
            for tag, sz in sizes:
                fig, ax = plt.subplots(figsize=sz)
                draw_bicolor(ax, x_over_c, vraw, x_over_c, lw=1.0)
                ax.set_xlim(pad_lo, pad_hi)
                ax.set_xlabel("x/c")
                ax.set_ylabel(label)

                base = outdir / f"{fname}_vs_xc_{tag}"
                fig.tight_layout()
                fig.savefig(base.with_suffix(".pdf"))
                pdf.savefig(fig)
                plt.close(fig)

            # vs s
            for tag, sz in sizes:
                fig, ax = plt.subplots(figsize=sz)
                draw_bicolor(ax, s_unit, vraw, x_over_c, lw=1.0)
                ax.set_xlim(-1.0, 1.0)
                ax.set_xlabel("s")
                ax.set_ylabel(label)

                base = outdir / f"{fname}_vs_s_{tag}"
                fig.tight_layout()
                fig.savefig(base.with_suffix(".pdf"))
                pdf.savefig(fig)
                plt.close(fig)

    print(f"Done. Individual PDFs and multi-page PDF written to: {pdf_path.resolve()}")



if __name__ == "__main__":
    main()
