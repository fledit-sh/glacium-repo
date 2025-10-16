#!/usr/bin/env python3
"""
mesh_report.py – Mesh‑Qualitätsbericht mit Screenshots
=====================================================
Erstellt einen HTML‑Report mit
* Statistiken & Histogrammen ausgewählter Qualitätsmetriken
* Full‑ und Zoom‑Screenshots je Metrik (Top‑Down, Parallel)
* Wireframe‑Darstellungen (schwarze Edges, weißer Hintergrund)

Verwendung
----------
python mesh_report.py mesh.cas \
                 --zoom -0.5 0.8 -0.5 0.5 \
                 -o report.html \
                 --png-dir imgs

Abhängigkeiten
--------------
pyvista ≥ 0.46, numpy, pandas, matplotlib
"""

from __future__ import annotations

import argparse
import base64
import os
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


class _OptionalModuleProxy:
    """Proxy raising an informative ImportError when accessed."""

    def __init__(self, name: str, error: Exception):
        self._name = name
        self._error = error

    def __getattr__(self, item):  # pragma: no cover - exercised when deps missing
        raise ImportError(
            f"{self._name} is required for glacium.utils.postprocess_mesh_html"
        ) from self._error


try:  # pragma: no cover - optional dependency for lightweight installs
    import pandas as pd  # type: ignore[import-not-found]
except Exception as exc:  # pragma: no cover - fallback when pandas missing
    pd = _OptionalModuleProxy("pandas", exc)  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency for lightweight installs
    import pyvista as pv  # type: ignore[import-not-found]
except Exception as exc:  # pragma: no cover - fallback when pyvista missing
    pv = _OptionalModuleProxy("pyvista", exc)  # type: ignore[assignment]

# --------------------------------------------------
# Einstellungen
# --------------------------------------------------
QUALITY_MEASURES = [
    "scaled_jacobian",
    "aspect_ratio",
    "skew",
    "warpage",
    "volume",
]
WINDOW_SIZE = (1600, 1200)

# --------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------

def make_topdown(bounds):
    """Erzeugt eine parallele Top‑Down‑Kamera für gegebene Bounds."""
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    cx, cy, cz = (xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2
    cam = pv.Camera()
    cam.position = (cx, cy, cz + 10.0)
    cam.focal_point = (cx, cy, cz)
    cam.view_up = (0, 1, 0)
    cam.parallel_projection = True
    cam.parallel_scale = max(xmax - xmin, ymax - ymin) / 2
    return cam


def collect_quality(ds: pv.DataSet, measures):
    """Liefert dict {measure: ndarray} für alle gewünschten Metriken."""
    data = {}
    if hasattr(ds, "cell_quality"):
        q = ds.cell_quality(measures)
        for m in measures:
            data[m] = q.cell_data[m]
    else:  # Kompatibilität PyVista <0.45
        for m in measures:
            q = ds.compute_cell_quality(m)
            data[m] = q.cell_data["CellQuality"]
    return data


def screenshot_colored(mesh: pv.DataSet, scalars: np.ndarray, title: str, bounds, zoom_box=None):
    clim = np.percentile(scalars, [5, 95])
    p = pv.Plotter(off_screen=True, window_size=WINDOW_SIZE)
    p.add_mesh(mesh, scalars=scalars, cmap="viridis", clim=clim, show_edges=False)
    p.add_scalar_bar(title=title)
    if zoom_box is not None:
        p.add_mesh(zoom_box, color="red", style="wireframe", line_width=3)
    p.camera = make_topdown(bounds)
    p.show(auto_close=False)
    img = p.screenshot(return_img=True)
    p.close()
    return img


def screenshot_wireframe(mesh: pv.DataSet, bounds):
    p = pv.Plotter(off_screen=True, window_size=WINDOW_SIZE)
    p.background_color = "white"
    p.add_mesh(mesh, color="white", show_edges=True, edge_color="black")
    p.camera = make_topdown(bounds)
    p.show(auto_close=False)
    img = p.screenshot(return_img=True)
    p.close()
    return img


def img_tag(img: np.ndarray) -> str:
    buf = BytesIO()
    plt.imsave(buf, img)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"<img src='data:image/png;base64,{b64}' style='max-width:100%;height:auto;'/>"


def histograms_html(df: pd.DataFrame) -> str:
    parts = []
    for col in df.columns:
        fig, ax = plt.subplots()
        ax.hist(df[col].dropna(), bins=50)
        ax.set_title(col.replace("_", " ").title())
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        parts.append(f"<h3>{col}</h3><img src='data:image/png;base64,{b64}'/>")
    return "\n".join(parts)


def build_html(meshfile: str, df: pd.DataFrame, shots: dict[str, tuple[np.ndarray, np.ndarray]], wf_full, wf_zoom):
    stats_html = df.describe().to_html(classes="stats", float_format="{:0.3g}".format)
    hist_html = histograms_html(df)

    shot_sections = []
    for m, (full_img, zoom_img) in shots.items():
        title = m.replace("_", " ").title()
        shot_sections.append(
            f"<h3>{title} – Full</h3>{img_tag(full_img)}"
            f"<h3>{title} – Zoom</h3>{img_tag(zoom_img)}"
        )

    wf_html = (
        "<h3>Wireframe – Full</h3>" + img_tag(wf_full) +
        "<h3>Wireframe – Zoom</h3>" + img_tag(wf_zoom)
    )

    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'>
<title>Mesh Report – {os.path.basename(meshfile)}</title>
<style>
body{{font-family:Arial,sans-serif;margin:20px}}
h1,h2{{color:#003366}}
.stats{{border-collapse:collapse}}
.stats th,.stats td{{border:1px solid #999;padding:4px 8px;text-align:right}}
.stats thead th{{background:#ddeeff}}
</style></head><body>
<h1>Mesh Quality Report</h1>
<p><strong>File:</strong> {os.path.basename(meshfile)}</p>
<h2>Statistics</h2>
{stats_html}
<h2>Histograms</h2>
{hist_html}
<h2>Mesh Screenshots</h2>
{''.join(shot_sections)}
<h2>Wireframe Views</h2>
{wf_html}
</body></html>"""

# --------------------------------------------------
# Hauptprogramm
# --------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Generate mesh report with screenshots and wireframes")
    ap.add_argument("meshfile", help="Mesh file (.cas, .grid, .vtu, ...)")
    ap.add_argument("-o", "--output", default="mesh_report.html", help="Output HTML report")
    ap.add_argument("--zoom", nargs=4, type=float, metavar=("XMIN", "XMAX", "YMIN", "YMAX"),
                    help="XY bounds of zoom window (Z inferred from mesh bounds)")
    ap.add_argument("--measures", nargs="*", default=QUALITY_MEASURES, help="Quality measures")
    ap.add_argument("--png-dir", help="Optional directory to save PNG screenshots")
    args = ap.parse_args()

    # Mesh laden
    obj = pv.read(args.meshfile)
    mesh = obj.combine() if isinstance(obj, pv.MultiBlock) else obj

    # Qualitäts­metriken für Voll­mesh
    qual_full = collect_quality(mesh, args.measures)
    df = pd.DataFrame(qual_full)

    # Zoom‑Fenster bestimmen
    full_bounds = mesh.bounds
    if args.zoom:
        xmin, xmax, ymin, ymax = map(float, args.zoom)
    else:
        dx, dy = full_bounds[1]-full_bounds[0], full_bounds[3]-full_bounds[2]
        xmin, xmax = full_bounds[0]+0.35*dx, full_bounds[1]-0.35*dx
        ymin, ymax = full_bounds[2]+0.35*dy, full_bounds[3]-0.35*dy
    zmin, zmax = full_bounds[4], full_bounds[5]
    zoom_bounds = (xmin, xmax, ymin, ymax, zmin, zmax)

    zoom_box = pv.Box(bounds=zoom_bounds)
    mesh_zoom = mesh.clip_box(zoom_bounds, invert=False)

    # Qualitätsmetriken für Zoom‑Mesh separat berechnen
    qual_zoom = collect_quality(mesh_zoom, args.measures)

    # PNG‑Verzeichnis
    out_dir = Path(args.png_dir) if args.png_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    # Screenshots erzeugen
    screenshots = {}
    for m in args.measures:
        full_shot = screenshot_colored(mesh, qual_full[m], m, full_bounds, zoom_box)
        zoom_shot = screenshot_colored(mesh_zoom, qual_zoom[m], m, zoom_bounds)
        screenshots[m] = (full_shot, zoom_shot)
        if out_dir:
            plt.imsave(out_dir / f"{m}_full.png", full_shot)
            plt.imsave(out_dir / f"{m}_zoom.png", zoom_shot)

    # Wireframes
    wf_full = screenshot_wireframe(mesh, full_bounds)
    wf_zoom = screenshot_wireframe(mesh_zoom, zoom_bounds)
    if out_dir:
        plt.imsave(out_dir / "wireframe_full.png", wf_full)
        plt.imsave(out_dir / "wireframe_zoom.png", wf_zoom)

    # HTML‑Bericht schreiben
    html = build_html(args.meshfile, df, screenshots, wf_full, wf_zoom)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report written to {args.output}")
    if out_dir:
        print(f"PNGs saved in {out_dir.resolve()}")

if __name__ == "__main__":
    main()
