#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_auto_cp_normals.py (compact)
- Reads merged.dat (Zone 1) to get x,y and Cp (column name default "Cp"; fallback compute Cp).
- Computes INLET freestream (v∞, ρ∞, p∞, q∞) from SOLN file for legend / Cp fallback.
- Normal plot: profile black, normals outward, |Cp|-scaled; Cp>0 red, Cp<0 blue.
- Cp curve: x/c vs Cp, colored by sign; CSV optional.
"""

import argparse, re, zipfile
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import numpy as np
import matplotlib.pyplot as plt

# ---------- helpers ----------

def _norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.strip().lower())

def _find_var_fuzzy(var_names: List[str], *needles: str) -> Optional[int]:
    keys = [_norm_key(v) for v in var_names]
    for n in needles:
        if not n: continue
        nn = _norm_key(n)
        for i,k in enumerate(keys):
            if k == nn or nn in k:
                return i
    return None

def _read_all_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")

def _open_maybe_zip(path: Path) -> str:
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p, "r") as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".dat")]
            if not names:
                raise ValueError("ZIP enthält keine .dat-Datei")
            import re as _re
            pref = [n for n in names if _re.search(r"soln\.fensap\.\d+\.dat$", Path(n).name, _re.I)]
            pick = pref[0] if pref else names[0]
            with zf.open(pick, "r") as fh:
                return fh.read().decode("utf-8", errors="replace")
    return _read_all_text(p)

def _parse_variables(lines: List[str]) -> Tuple[List[str], Dict[str,int]]:
    i = next((k for k, ln in enumerate(lines) if ln.lstrip().upper().startswith("VARIABLES")), None)
    if i is None: raise ValueError("VARIABLES-Zeile nicht gefunden")
    buf = lines[i]; j = i+1
    while j < len(lines) and not lines[j].lstrip().upper().startswith("ZONE"):
        buf += " " + lines[j]; j += 1
    cols = re.findall(r'"([^"]+)"', buf)
    var_names = [c.strip() for c in cols]
    return var_names, {name:i for i,name in enumerate(var_names)}

def _iter_zones(lines: List[str]) -> List[Tuple[int,int]]:
    idxs = [i for i,ln in enumerate(lines) if ln.lstrip().upper().startswith("ZONE")]
    if not idxs: return []
    idxs.append(len(lines))
    return [(idxs[i], idxs[i+1]) for i in range(len(idxs)-1)]

_num_line_re = re.compile(r'^[\s\+\-]?(?:\d|\.)')

def _read_zone_data(lines: List[str], start: int, end: int, nvars: int) -> Tuple[np.ndarray, List[List[int]]]:
    # Join header continuation lines to read N
    header_ext = lines[start]
    for look in range(start+1, min(end, start+12)):
        s = lines[look].strip()
        if _num_line_re.match(s) or s.startswith('"'):
            break
        header_ext += " " + s
    mN = re.search(r"\bN\s*=\s*(\d+)", header_ext, re.I)
    if not mN: raise ValueError("N= nicht im ZONE-Header gefunden")
    N = int(mN.group(1))
    floats = []; k = start+1; target = N*nvars
    while k < end and len(floats) < target:
        s = lines[k].strip()
        if s:
            s = re.sub(r"(?<=\d)([+\-]\d{2,})", r"e\1", s)
            for t in s.split():
                if len(floats) >= target: break
                try: floats.append(float(t))
                except: pass
        k += 1
    if len(floats) < target: raise ValueError(f"Knoten-Daten zu kurz: {len(floats)} < {target}")
    nodes = np.array(floats[:target], float).reshape(N, nvars)
    return nodes, []

def parse_first_zone(path: Path) -> Tuple[np.ndarray, List[str], Optional[np.ndarray], Dict]:
    lines = _read_all_text(path).splitlines()
    var_names, _ = _parse_variables(lines)
    nvars = len(var_names)
    zones = _iter_zones(lines)
    if not zones: raise ValueError("Keine ZONEs gefunden")
    s,e = zones[0]
    nodes, edges = _read_zone_data(lines, s, e, nvars)
    conn = np.asarray(edges, int) if edges else None
    return nodes, var_names, conn, {"lines": lines, "var_names": var_names}

# ---------- physics ----------

def _mean_safe(v: np.ndarray) -> float:
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    return float(np.nanmean(v)) if v.size else float("nan")

def _infer_inlet(lines: List[str], var_names: List[str], inlet_name: str="INLET") -> Dict[str,float]:
    import re as _re
    pat = _re.compile(r't\s*=\s*"[^"]*(?:' + _re.escape(inlet_name) + r'|farfield)[^"]*"', _re.I)
    z_ranges = _iter_zones(lines)
    pick = None
    for s,e in z_ranges:
        header_ext = lines[s]
        for look in range(s+1, min(e, s+12)):
            nxt = lines[look].strip()
            if nxt.startswith('"') or _num_line_re.match(nxt): break
            header_ext += " " + nxt
        if pat.search(header_ext):
            pick = (s,e); break
    if not pick: raise ValueError(f"INLET-Zone '{inlet_name}' nicht gefunden")
    nvars = len(var_names)
    nodes, _ = _read_zone_data(lines, pick[0], pick[1], nvars)

    xi = _find_var_fuzzy(var_names, "x")
    if xi is None: raise ValueError("x nicht gefunden im INLET")
    x = nodes[:, xi]
    xmin, xmax = np.nanmin(x), np.nanmax(x)
    tolx = max(1e-6*(xmax-xmin), 1e-9)
    slab = nodes[(x - xmin) <= tolx]; 
    if slab.size == 0: slab = nodes

    pi   = _find_var_fuzzy(var_names, "pressure", "p", "staticpressure")
    rhoi = _find_var_fuzzy(var_names, "density", "rho")
    qi   = _find_var_fuzzy(var_names, "q", "q_inf", "dynamicpressure", "dynpressure", "dynpress")
    v1i  = _find_var_fuzzy(var_names, "v1velocity")
    v2i  = _find_var_fuzzy(var_names, "v2velocity")
    v3i  = _find_var_fuzzy(var_names, "v3velocity")
    ui   = _find_var_fuzzy(var_names, "u", "velocityx")
    vi   = _find_var_fuzzy(var_names, "v", "velocityy")
    wi   = _find_var_fuzzy(var_names, "w", "velocityz")
    vmag = _find_var_fuzzy(var_names, "velocitymagnitude", "velmag", "speed", "magv")

    def mean_at(idx):
        if idx is None: return float("nan")
        v = slab[:, idx]; v = v[np.isfinite(v)]
        return float(np.nanmean(v)) if v.size else float("nan")

    p_inf   = mean_at(pi)
    rho_inf = mean_at(rhoi)

    if qi is not None:
        q_inf = mean_at(qi)
        v_inf = (np.sqrt(2*q_inf/rho_inf) if np.isfinite(q_inf) and np.isfinite(rho_inf) and rho_inf>0 else float("nan"))
    else:
        comps = []
        for idx in (v1i, v2i, v3i):
            if idx is not None: comps.append(slab[:, idx])
        if not comps:
            for idx in (ui, vi, wi):
                if idx is not None: comps.append(slab[:, idx])
        if comps:
            V = np.column_stack(comps).astype(float)
            v_inf = float(np.nanmean(np.linalg.norm(V, axis=1)))
        elif vmag is not None:
            v_inf = mean_at(vmag)
        else:
            v_inf = float("nan")
        q_inf = (0.5 * rho_inf * v_inf**2) if np.isfinite(rho_inf) and np.isfinite(v_inf) else float("nan")

    return dict(p_inf=p_inf, q_inf=q_inf, rho_inf=rho_inf, v_inf=v_inf)

def outward_normals(x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    dx = np.gradient(x); dy = np.gradient(y)
    tlen = np.hypot(dx, dy); tlen[tlen == 0] = 1.0
    tx = dx / tlen; ty = dy / tlen
    nx = -ty; ny = tx
    area2 = np.trapz(x*np.gradient(y) - y*np.gradient(x))
    sign = -1.0 if area2 < 0 else 1.0
    nx *= sign; ny *= sign
    cx, cy = np.nanmean(x), np.nanmean(y)
    if np.nanmean(nx*(x-cx) + ny*(y-cy)) < 0:
        nx = -nx; ny = -ny
    return nx, ny

def compute_cp_on_wall(nodes: np.ndarray, var_names: List[str], p_inf: float, q_inf: float,
                       p_name: Optional[str]=None, cp_name: Optional[str]=None) -> np.ndarray:
    if cp_name:
        ci = _find_var_fuzzy(var_names, cp_name)
        if ci is not None: return nodes[:, ci]
    pi = _find_var_fuzzy(var_names, p_name or "pressure", "p", "staticpressure")
    if pi is None: raise ValueError("p nicht gefunden und Cp-Variable nicht verfügbar")
    if not np.isfinite(q_inf) or abs(q_inf) < 1e-300:
        raise ValueError("q_inf ist nicht endlich/nicht > 0; Cp-Berechnung nicht möglich")
    return (nodes[:, pi] - p_inf) / q_inf

# ---------- plotting ----------

def _legend_string(v_inf: float, rho_inf: float, p_inf: float, q_inf: float) -> str:
    def fmt(val):
        return "n/a" if not np.isfinite(val) else f"{val:.4g}"
    # Einheiten als MathText (funktioniert ohne externes LaTeX):
    u_v   = r"\,\mathrm{m\,s^{-1}}"
    u_rho = r"\,\mathrm{kg\,m^{-3}}"
    u_pq  = r"\,\mathrm{Pa}"
    return (
        r"$v_\infty$ = "   + (r"$" + fmt(v_inf)   + u_v   + r"$") + "\n" +
        r"$\rho_\infty$ = "+ (r"$" + fmt(rho_inf) + u_rho + r"$") + "\n" +
        r"$p_\infty$ = "   + (r"$" + fmt(p_inf)   + u_pq  + r"$") + "\n" +
        r"$q_\infty$ = "   + (r"$" + fmt(q_inf)   + u_pq  + r"$")
    )


def _concat_edges_to_order(edges, N):
    if not edges: return np.arange(N, int)
    from collections import defaultdict
    g = defaultdict(list)
    for a,b in edges:
        if 0 <= a < N and 0 <= b < N:
            g[a].append(b); g[b].append(a)
    start = next((i for i in range(N) if len(g[i])==1), 0)
    seen = {start}; cur = start; order = [start]
    while True:
        nxts = [v for v in g[cur] if v not in seen]
        if not nxts: break
        cur = nxts[0]; seen.add(cur); order.append(cur)
    if len(order) < N: order.extend([i for i in range(N) if i not in seen])
    return np.asarray(order, int)

def plot_cp_normals_png(nodes, var_names, conn, out_png, cp,
                        x_name="x", y_name="y", base_len=0.0, extra_len=0.05,
                        scale_mode="absolute", legend_text=None, dpi=200):
    xi = _find_var_fuzzy(var_names, x_name); yi = _find_var_fuzzy(var_names, y_name)
    if xi is None or yi is None: raise ValueError("x/y nicht gefunden")
    x = nodes[:, xi].astype(float); y = nodes[:, yi].astype(float)
    order = _concat_edges_to_order(conn.tolist(), len(x)) if conn is not None and len(conn)>0 else np.arange(len(x))
    x = x[order]; y = y[order]; cp = cp[order]
    nx, ny = outward_normals(x, y)
    abs_cp = np.abs(cp)
    if scale_mode == "normalized":
        cpmax = np.nanmax(abs_cp) if np.isfinite(abs_cp).any() else 1.0
        mag = base_len + extra_len * (abs_cp / (cpmax if cpmax>0 else 1.0))
    else:
        mag = base_len + extra_len * abs_cp
    x2 = x + nx*mag; y2 = y + ny*mag

    plt.figure()
    plt.plot(x, y, color="k", lw=1.2)
    for i in range(len(x)):
        color = "r" if cp[i] >= 0 else "b"
        plt.plot([x[i], x2[i]], [y[i], y2[i]], lw=0.9, color=color)
    plt.axis("equal"); plt.xlabel("x"); plt.ylabel("y")
    if legend_text: plt.legend([legend_text], loc="best", frameon=True)
    plt.tight_layout(); plt.savefig(out_png, dpi=dpi); plt.close()

def save_cp_curve_csv(nodes, var_names, cp, out_csv):
    xi = _find_var_fuzzy(var_names, "x"); yi = _find_var_fuzzy(var_names, "y")
    if xi is None or yi is None: raise ValueError("x/y nicht gefunden")
    x = nodes[:, xi].astype(float); y = nodes[:, yi].astype(float)
    xmin, xmax = np.nanmin(x), np.nanmax(x); c = xmax - xmin if np.isfinite(xmin) and np.isfinite(xmax) else np.nan
    x_over_c = (x - xmin) / c if np.isfinite(c) and c>0 else np.full_like(x, np.nan)
    ds = np.hypot(np.gradient(x), np.gradient(y)); s = np.cumsum(ds); s -= s[0]
    order = np.argsort(x)
    data = np.column_stack([x[order], y[order], x_over_c[order], s[order], cp[order]])
    np.savetxt(out_csv, data, delimiter=",", header="x,y,x_over_c,s,cp", comments="")

def plot_cp_curve_png(nodes, var_names, cp, out_png, legend_text=None, dpi=200):
    xi = _find_var_fuzzy(var_names, "x")
    if xi is None: raise ValueError("x nicht gefunden")
    x = nodes[:, xi].astype(float)
    xmin, xmax = np.nanmin(x), np.nanmax(x); c = xmax - xmin if np.isfinite(xmin) and np.isfinite(xmax) else np.nan
    x_over_c = (x - xmin) / c if np.isfinite(c) and c>0 else np.full_like(x, np.nan)
    order = np.argsort(x); xo = x_over_c[order]; cpo = cp[order]
    plt.figure()
    for i in range(len(xo)-1):
        seg_x, seg_y = [xo[i], xo[i+1]], [cpo[i], cpo[i+1]]
        color = "r" if (cpo[i] + cpo[i+1]) >= 0 else "b"
        plt.plot(seg_x, seg_y, lw=1.2, color=color)
    plt.gca().invert_yaxis(); plt.xlabel(r"$x/c$"); plt.ylabel(r"$C_p$")
    if legend_text: plt.legend([legend_text], loc="best", frameon=True)
    plt.tight_layout(); plt.savefig(out_png, dpi=dpi); plt.close()

# ---------- cli ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solution", type=Path, required=True)
    ap.add_argument("--merged-in", type=Path, required=True)
    ap.add_argument("--png-out", type=Path, required=True)
    ap.add_argument("--cp-png-out", type=Path, default=None)
    ap.add_argument("--csv-out", type=Path, default=None)
    ap.add_argument("--inlet-name", type=str, default="INLET")
    ap.add_argument("--p-name", type=str, default=None)
    ap.add_argument("--cp-name", type=str, default="Cp")
    ap.add_argument("--xname", type=str, default="x"); ap.add_argument("--yname", type=str, default="y")
    ap.add_argument("--base", type=float, default=0.0); ap.add_argument("--extra", type=float, default=0.05)
    ap.add_argument("--scale-mode", choices=["absolute","normalized"], default="absolute")
    ap.add_argument("--legend", choices=["on","off"], default="on")
    ap.add_argument("--latex", choices=["on","off"], default="on")
    ap.add_argument("--dpi", type=int, default=200)
    args = ap.parse_args()

    if args.latex == "on":
        try:
            plt.rcParams["text.usetex"] = True
        except Exception:
            plt.rcParams["text.usetex"] = False  # fallback auf MathText
    else:
        plt.rcParams["text.usetex"] = False

    # merged
    nodes, var_names, conn, _ = parse_first_zone(args.merged_in)

    # inlet from SOLN
    sol_text = _open_maybe_zip(args.solution)
    lines_sol = sol_text.splitlines()
    var_names_sol, _ = _parse_variables(lines_sol)
    atm = _infer_inlet(lines_sol, var_names_sol, inlet_name=args.inlet_name)
    p_inf = atm.get("p_inf", np.nan); q_inf = atm.get("q_inf", np.nan)
    rho_inf = atm.get("rho_inf", np.nan); v_inf = atm.get("v_inf", np.nan)
    legend_text = _legend_string(v_inf, rho_inf, p_inf, q_inf) if args.legend == "on" else None

    # Cp
    cp = compute_cp_on_wall(nodes, var_names, p_inf, q_inf, p_name=args.p_name, cp_name=args.cp_name)

    # plots
    plot_cp_normals_png(nodes, var_names, conn, args.png_out, cp,
                        x_name=args.xname, y_name=args.yname,
                        base_len=args.base, extra_len=args.extra,
                        scale_mode=args.scale_mode, legend_text=legend_text, dpi=args.dpi)
    if args.csv_out: save_cp_curve_csv(nodes, var_names, cp, args.csv_out)
    if args.cp_png_out: plot_cp_curve_png(nodes, var_names, cp, args.cp_png_out, legend_text=legend_text, dpi=args.dpi)

    print("Legend:\n", legend_text)
    print("Normalen-Plot:", args.png_out)
    if args.cp_png_out: print("Cp-Plot:", args.cp_png_out)
    if args.csv_out: print("Cp-CSV:", args.csv_out)

if __name__ == "__main__":
    main()
