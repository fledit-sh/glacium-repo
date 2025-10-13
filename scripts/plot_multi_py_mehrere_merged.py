from __future__ import annotations
import argparse, re, sys
from pathlib import Path
from typing import List, Tuple, Dict, Iterable
import numpy as np
import matplotlib.pyplot as plt

# -------------------- Utilities --------------------
_num_line_re = re.compile(r'^[\s\+\-]?(?:\d|\.)')
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
    s = clean_label(name)
    s = s.replace(":", "__")
    s = re.sub(r'[<>:"/\\|?*]', "_", s)
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "var"

# -------------------- Parsing merged.dat (first ZONE incl. connectivity) --------------------

def _parse_variables(lines: List[str]) -> Tuple[List[str], Dict[str, int]]:
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
    return names, {_normalize(v): k for k, v in enumerate(names)}


def _read_first_zone_with_conn(path: Path) -> Tuple[np.ndarray, np.ndarray, List[str], Dict[str, int]]:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()

    var_names, var_map = _parse_variables(lines)
    nvars = len(var_names)

    z0 = next((i for i, ln in enumerate(lines) if ln.lstrip().upper().startswith("ZONE")), None)
    if z0 is None:
        raise ValueError("No ZONE header found")
    z1 = next((i for i in range(z0 + 1, len(lines)) if lines[i].lstrip().upper().startswith("ZONE")), len(lines))

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
    ztype_m = re.search(r"ZONETYPE\s*=\s*([A-Za-z0-9_]+)", header_ext, flags=re.I)
    ztype = ztype_m.group(1).upper() if ztype_m else ""
    if not mN:
        raise ValueError("N= not found in first ZONE header")
    N = int(mN.group(1)); E = int(mE.group(1)) if mE else 0

    floats: List[float] = []
    while k < z1 and len(floats) < N * nvars:
        s = lines[k].strip(); k += 1
        if not s:
            continue
        s = re.sub(r"(?<=\d)([+\-]\d{2,})", r"e\1", s)
        for t in s.split():
            if len(floats) >= N * nvars:
                break
            try:
                floats.append(float(t))
            except ValueError:
                pass
    if len(floats) < N * nvars:
        raise ValueError(f"Node data too short: {len(floats)} < {N*nvars}")
    nodes = np.array(floats[: N * nvars], dtype=float).reshape(N, nvars)

    conn = np.empty((0, 2), dtype=int)
    if ztype == "FELINESEG" and E > 0:
        edges = []; count = 0
        while k < z1 and count < E:
            toks = lines[k].strip().split(); k += 1
            if len(toks) == 2 and all(re.fullmatch(r"[+\-]?\d+", t) for t in toks):
                a = int(toks[0]) - 1; b = int(toks[1]) - 1
                if 0 <= a < N and 0 <= b < N:
                    edges.append([a, b]); count += 1
        if edges:
            conn = np.array(edges, dtype=int)

    return nodes, conn, var_names, var_map

# -------------------- Connectivity ordering --------------------

def order_from_connectivity(N: int, conn: np.ndarray) -> np.ndarray:
    if conn is None or conn.size == 0:
        return np.arange(N, dtype=int)
    from collections import defaultdict
    adj = defaultdict(list)
    for a, b in conn:
        a = int(a); b = int(b)
        adj[a].append(b); adj[b].append(a)

    visited = set(); best_component = []
    for start in adj.keys():
        if start in visited:
            continue
        comp = []; stack = [start]; visited.add(start)
        while stack:
            u = stack.pop(); comp.append(u)
            for v in adj[u]:
                if v not in visited:
                    visited.add(v); stack.append(v)
        if len(comp) > len(best_component):
            best_component = comp

    start = min(best_component) if best_component else 0
    order = [start]; used_edges = set(); cur = start
    steps = 0; max_steps = max(4 * len(conn), 10)
    while steps < max_steps:
        steps += 1
        nxt = None
        for nb in adj[cur]:
            e = tuple(sorted((cur, nb)))
            if e not in used_edges:
                used_edges.add(e); nxt = nb; break
        if nxt is None:
            break
        order.append(nxt); cur = nxt

    if len(order) < N:
        seen = set(order)
        order.extend([i for i in range(N) if i not in seen])
    return np.array(order, dtype=int)

# -------------------- Orientation & s helpers --------------------

def rotate_start_argmax_x(*arrays):
    x = arrays[0]
    idx = int(np.nanargmax(x))
    def rot(a):
        return np.concatenate([a[idx:], a[:idx]])
    return tuple(rot(a) for a in arrays)


def enforce_clockwise(*arrays):
    x, y = arrays[0], arrays[1]
    if x.size >= 3:
        xs = np.concatenate([x, x[:1]])
        ys = np.concatenate([y, y[:1]])
        area = 0.5 * np.sum(xs[:-1] * ys[1:] - xs[1:] * ys[:-1])
        if area > 0:  # CCW
            return tuple(a[::-1] for a in arrays)
    return arrays


def arclength(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    dx = np.diff(x); dy = np.diff(y)
    return np.concatenate([[0.0], np.cumsum(np.sqrt(dx * dx + dy * dy))])


def scale_s_minus1_to_1(s: np.ndarray) -> np.ndarray:
    s0, s1 = float(s[0]), float(s[-1])
    if not (np.isfinite(s0) and np.isfinite(s1)) or s1 == s0:
        return np.zeros_like(s)
    return -1.0 + 2.0 * (s - s0) / (s1 - s0)

# -------------------- Plotting helpers --------------------

COLORS_DEFAULT = (
    "C0","C1","C2","C3","C4","C5","C6","C7","C8","C9",
)


def _iter_colors(n: int, user_list: Iterable[str] | None) -> List[str]:
    if user_list:
        lst = [c.strip() for c in user_list if c.strip()]
        if not lst:
            lst = list(COLORS_DEFAULT)
    else:
        lst = list(COLORS_DEFAULT)
    if n <= len(lst):
        return lst[:n]
    # repeat if more files than colors
    reps = (n + len(lst) - 1) // len(lst)
    return (lst * reps)[:n]

# -------------------- Data container --------------------

class Dataset:
    def __init__(self, path: Path):
        self.path = path
        nodes, conn, var_names, var_map = _read_first_zone_with_conn(path)
        self.var_names = var_names
        self.var_map = var_map
        N = nodes.shape[0]
        order = order_from_connectivity(N, conn)

        x_idx = var_map.get("x"); y_idx = var_map.get("y")
        if x_idx is None:
            raise SystemExit(f"X not found in VARIABLES for {path}")
        x = nodes[:, x_idx].astype(float)
        y = nodes[:, y_idx].astype(float) if y_idx is not None else np.zeros_like(x)

        nodes_o = nodes[order, :]
        x_o = x[order]; y_o = y[order]

        arrays = (x_o, y_o, nodes_o)
        arrays = rotate_start_argmax_x(*arrays)
        arrays = enforce_clockwise(*arrays)
        arrays = rotate_start_argmax_x(*arrays)
        x_o, y_o, nodes_o = arrays

        c = float(np.nanmax(x_o))
        if not np.isfinite(c) or c == 0.0:
            raise SystemExit(f"max(X) invalid; cannot compute x/c for {path}")

        self.x_over_c = x_o / c
        self.y_over_c = y_o / c
        self.s = scale_s_minus1_to_1(arclength(x_o, y_o))
        self.nodes_o = nodes_o
        self.y_idx = y_idx

    def get_var(self, idx: int) -> np.ndarray:
        return self.nodes_o[:, idx].astype(float)

# -------------------- Main --------------------


def main():
    from matplotlib.backends.backend_pdf import PdfPages

    ap = argparse.ArgumentParser(description="Overlay multiple merged.dat files. One color per file.")
    ap.add_argument("merged", type=Path, nargs="+", help="one or more merged.dat (Tecplot ASCII)")
    ap.add_argument("--labels", nargs="*", default=None, help="legend labels (default: file stem)")
    ap.add_argument("--colors", nargs="*", default=None, help="matplotlib colors per file, e.g. C0 C1 k r")
    ap.add_argument("--outdir", type=Path, default=Path("plots_multi"))
    ap.add_argument("--style", type=str, default="science,ieee", help='Matplotlib styles (default). Use "" to disable.')
    args = ap.parse_args()

    outdir = args.outdir; outdir.mkdir(parents=True, exist_ok=True)

    # Style config (no external LaTeX)
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
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42

    # Load datasets
    datasets: List[Dataset] = []
    for p in args.merged:
        try:
            datasets.append(Dataset(p))
        except Exception as e:
            print(f"[skip] {p}: {e}")
    if not datasets:
        raise SystemExit("No valid datasets loaded.")

    # Labels & colors
    n = len(datasets)
    labels = args.labels if args.labels and len(args.labels) == n else [d.path.stem for d in datasets]
    colors = _iter_colors(n, args.colors)

    # Variable list = intersection to avoid mismatched VARS
    var_lists = [set(d.var_names) for d in datasets]
    common_vars = list(sorted(set.intersection(*var_lists)))

    # Build var index maps aligned by name across datasets
    var_indices = []
    for d in datasets:
        m = {name: d.var_names.index(name) for name in common_vars}
        var_indices.append(m)

    sizes = [("full", (6.3, 3.9)), ("dbl", (3.15, 2.0))]
    pdf_path = outdir / "overlay_all_plots.pdf"

    # X-axis padding from global bounds (x/c)
    xmin = min(float(np.nanmin(d.x_over_c)) for d in datasets)
    xmax = max(float(np.nanmax(d.x_over_c)) for d in datasets)
    pad_lo = xmin - 0.05; pad_hi = xmax + 0.05
    if not np.isfinite(pad_lo): pad_lo = -0.05
    if not np.isfinite(pad_hi): pad_hi = 1.05
    if pad_lo >= pad_hi: pad_lo, pad_hi = xmin - 0.05, xmin + 0.05

    with PdfPages(pdf_path) as pdf:
        # 0) Geometry overlay: y/c vs x/c (equal aspect)
        for tag, sz in sizes:
            fig, ax = plt.subplots(figsize=sz)
            for d, lab, col in zip(datasets, labels, colors):
                if d.y_idx is None:
                    continue
                ax.plot(d.x_over_c, d.y_over_c, lw=0.8, label=lab, color=col, linestyle="-")
            ax.set_xlim(pad_lo, pad_hi)
            ax.set_xlabel("x/c"); ax.set_ylabel("y/c")
            ax.set_aspect("equal", adjustable="box")
            ax.legend(frameon=False, ncol=2)
            base = outdir / f"geom_yc_vs_xc_overlay_{tag}"
            fig.tight_layout(); fig.savefig(base.with_suffix('.pdf')); pdf.savefig(fig); plt.close(fig)

        # 1) For every common variable: vs x/c and vs s overlays
        for vname in common_vars:
            # skip raw Y (redundant with geometry)
            # detect index from first dataset
            idx0 = datasets[0].var_names.index(vname)
            if datasets[0].y_idx is not None and idx0 == datasets[0].y_idx:
                continue

            label = clean_label(vname)
            fname = safe_name(vname)

            # vs x/c
            for tag, sz in sizes:
                fig, ax = plt.subplots(figsize=sz)
                for d, lab, col, idxmap in zip(datasets, labels, colors, var_indices):
                    i = idxmap[vname]
                    v = d.get_var(i)
                    ax.plot(d.x_over_c, v, lw=0.8, label=lab, color=col, linestyle="-")
                ax.set_xlim(pad_lo, pad_hi)
                ax.set_xlabel("x/c"); ax.set_ylabel(label)
                ax.legend(frameon=False, ncol=2)
                base = outdir / f"{fname}_vs_xc_overlay_{tag}"
                fig.tight_layout(); fig.savefig(base.with_suffix('.pdf')); pdf.savefig(fig); plt.close(fig)

            # vs s
            for tag, sz in sizes:
                fig, ax = plt.subplots(figsize=sz)
                for d, lab, col, idxmap in zip(datasets, labels, colors, var_indices):
                    i = idxmap[vname]
                    v = d.get_var(i)
                    ax.plot(d.s, v, lw=0.8, label=lab, color=col, linestyle="-")
                ax.set_xlim(-1.0, 1.0)
                ax.set_xlabel("s"); ax.set_ylabel(label)
                ax.legend(frameon=False, ncol=2)
                base = outdir / f"{fname}_vs_s_overlay_{tag}"
                fig.tight_layout(); fig.savefig(base.with_suffix('.pdf')); pdf.savefig(fig); plt.close(fig)

    print(f"Done. Overlay PDFs written to: {pdf_path.resolve()}")


if __name__ == "__main__":
    main()
