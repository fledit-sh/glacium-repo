#!/usr/bin/env python3
"""
mesh_report.py — HTML‑Report inklusive Mesh‑Screenshots
======================================================
Erstellt einen kompakten HTML‑Bericht mit
* Qualitätsstatistik (min/mean/max, Histogramme)
* Screenshots des Gitters, eingefärbt nach jeder Qualitätsmetrik

Aufruf
------
python mesh_report.py mesh.cas -o report.html [--png-dir imgs]

Abhängigkeiten
--------------
- pyvista  ≥ 0.46 (für `cell_quality` und Off‑screen‑Screenshots)
- numpy
- pandas
- matplotlib
"""

import argparse
import base64
import os
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyvista as pv

# Qualitätsmetriken – nach Bedarf ergänzen
QUALITY_MEASURES = [
    "scaled_jacobian",
    "aspect_ratio",
    "skew",
    "warpage",
    "volume",
]

def collect_quality(mesh: pv.DataSet, measures):
    """Dict {measure: ndarray} mit Qualitätswerten."""
    data = {}
    if hasattr(mesh, "cell_quality"):
        qmesh = mesh.cell_quality(measures)
        for m in measures:
            data[m] = qmesh.cell_data[m]
    else:  # Fallback für sehr alte PyVista‑Versionen
        for m in measures:
            q = mesh.compute_cell_quality(m)
            data[m] = q.cell_data["CellQuality"]
    return data

def embed_png(arr: np.ndarray) -> str:
    """PNG‑Bild (NumPy RGB‑Array) → Base64‑HTML‑IMG Tag."""
    buf = BytesIO()
    plt.imsave(buf, arr)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def make_histograms(df: pd.DataFrame) -> str:
    """HTML‑Fragment mit Histogrammen (Base64‑PNG)."""
    parts = []
    for col in df.columns:
        fig, ax = plt.subplots()
        ax.hist(df[col].dropna(), bins=50)
        ax.set_title(col.replace("_", " ").title())
        ax.set_xlabel(col)
        ax.set_ylabel("Count")
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        parts.append(f"<h3>{col}</h3><img src='data:image/png;base64,{b64}'/>")
    return "\n".join(parts)

def screenshot_mesh(mesh: pv.DataSet, scalars: np.ndarray, metric: str, size=(1600, 1200)) -> np.ndarray:
    """Erstellt ein Off‑screen‑Screenshot‑Array (RGB) für gegebene Skalare."""
    clim = np.percentile(scalars, [5, 95])
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.add_mesh(mesh, scalars=scalars, cmap="viridis", clim=clim, show_edges=False)
    pl.add_scalar_bar(title=metric.replace("_", " ").title())
    pl.view_isometric()
    pl.show(auto_close=False)  # benötigt für Screenshot‑Render
    img = pl.screenshot(return_img=True)
    pl.close()
    return img

def build_html_report(meshfile: str, df: pd.DataFrame, screenshots: dict[str, np.ndarray]) -> str:
    stats_table = df.describe().to_html(classes="stats", float_format="{:0.3g}".format)
    hist_html   = make_histograms(df)
    screen_html = "".join(
        f"<h3>{m.replace('_',' ').title()}</h3><img src='{embed_png(img)}'/>" for m, img in screenshots.items()
    )
    return f"""<!DOCTYPE html>
<html lang='en'><head><meta charset='utf-8'>
<title>Mesh Quality Report – {os.path.basename(meshfile)}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
h1, h2 {{ color: #003366; }}
.stats {{ border-collapse: collapse; }}
.stats th, .stats td {{ border: 1px solid #999; padding: 4px 8px; text-align: right; }}
.stats thead th {{ background: #ddeeff; }}
img {{ max-width: 100%; height: auto; }}
</style></head><body>
<h1>Mesh Quality Report</h1>
<p><strong>File:</strong> {os.path.basename(meshfile)}</p>
<h2>Summary Statistics</h2>
{stats_table}
<h2>Histograms</h2>
{hist_html}
<h2>Mesh Screenshots</h2>
{screen_html}
</body></html>"""

def main():
    p = argparse.ArgumentParser(description="Generate an HTML mesh quality report with screenshots")
    p.add_argument("meshfile", help="Mesh file (.cas, .grid, .vtu, ...)")
    p.add_argument("-o", "--output", default="mesh_report.html", help="Output HTML file")
    p.add_argument("-m", "--measures", nargs="*", default=QUALITY_MEASURES,
                   help="Quality measures (default: common set)")
    p.add_argument("--png-dir", help="Optional directory to save raw PNG screenshots")
    args = p.parse_args()

    obj  = pv.read(args.meshfile)
    mesh = obj.combine() if isinstance(obj, pv.MultiBlock) else obj
    qualities = collect_quality(mesh, args.measures)
    df = pd.DataFrame(qualities)

    # Screenshots
    screenshots = {}
    out_dir = Path(args.png_dir) if args.png_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
    for m in args.measures:
        img = screenshot_mesh(mesh, df[m].values, m)
        screenshots[m] = img
        if out_dir:
            plt.imsave(out_dir / f"{m}.png", img)

    # HTML
    html = build_html_report(args.meshfile, df, screenshots)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report written to {args.output} (cells: {len(df)}, metrics: {len(args.measures)})")
    if out_dir:
        print(f"PNG screenshots saved in {out_dir}")

if __name__ == "__main__":
    main()
