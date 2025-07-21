#!/usr/bin/env python3
"""
.py – Mehrfach‑Wireframe‑ und Zoom‑Screenshots eines Pointwise/Fluent‑Meshes
===============================================================================================
Erstellt für **beliebig viele** Zoom‑Fenster jeweils **zwei** PNG‑Bilder:
1. `wireframe_full_<n>.png`  – gesamtes Mesh mit rotem Rechteck des n‑ten Zooms
2. `wireframe_zoom_<n>.png` – Zoom‑Ausschnitt n mit denselben Kamera‑Einstellungen

Verwendung (fest codierte drei Fenster für Noel)
-----------------------------------------------
python wireframe_zoom_multi.py mesh.cas --outdir imgs

Generische Nutzung
------------------
python wireframe_zoom_multi.py mesh.cas \
        --xzoom -0.05 0.05 \
        --xzoom -0.4  0.5  \
        --xzoom -0.1  0.5  \
        --outdir imgs

* Für jedes ``--xzoom xmin xmax`` wird ``y`` automatisch **symmetrisch** um das
  Domain‑Zentrum gewählt, so dass das Fenster **genau 4:3** (1600 × 1200) hat.
* Funktioniert für `.cas`, `.grid`, `.vtu`, … – MultiBlock‑Meshes werden
  automatisch kombiniert.

Abhängigkeiten
--------------
pyvista ≥ 0.41, numpy (kommt mit PyVista)
"""

from __future__ import annotations
import argparse
from pathlib import Path
import pyvista as pv

WINDOW_SIZE = (1600, 1200)  # 4:3
ASPECT = WINDOW_SIZE[1] / WINDOW_SIZE[0]  # 0.75

# --------------------------------------------------
# Kamera – Top‑Down (Z‑Achse nach oben)
# --------------------------------------------------

def make_topdown(bounds: tuple[float, float, float, float, float, float]) -> pv.Camera:
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    cx, cy, cz = (xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2
    cam = pv.Camera()
    cam.position = (cx, cy, cz + 10.0)
    cam.focal_point = (cx, cy, cz)
    cam.view_up = (0, 1, 0)
    cam.parallel_projection = True
    cam.parallel_scale = max(xmax - xmin, ymax - ymin) / 2
    cam.clipping_range = (1e-3, 1e6)
    return cam

# --------------------------------------------------
# Screenshot‑Funktion
# --------------------------------------------------

def screenshot_wireframe(
    mesh: pv.DataSet,
    bounds: tuple[float, float, float, float, float, float],
    outfile: Path,
    highlight_bounds: tuple[float, float, float, float, float, float] | None = None,
) -> None:
    """Erstellt einen Wireframe‑Screenshot. Optional rotes Rechteck."""

    if mesh.n_cells == 0:
        print(f"⚠  {outfile.name}: Mesh enthält keine Zellen – übersprungen")
        return

    p = pv.Plotter(off_screen=True, window_size=WINDOW_SIZE)
    p.background_color = "white"

    # Kanten rendern –Röhren für gute Sichtbarkeit
    edges = mesh.extract_all_edges()
    p.add_mesh(edges, color="black", line_width=1, render_lines_as_tubes=True)

    # Optionale Markierung
    if highlight_bounds is not None:
        box = pv.Box(bounds=highlight_bounds)
        p.add_mesh(box, color="red", style="wireframe", line_width=3, render_lines_as_tubes=True)

    p.camera = make_topdown(bounds)
    p.show(screenshot=str(outfile))
    p.close()
    print("✔", outfile.name, "gespeichert")

# --------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------

def symmetric_y_for_aspect(
    full_ymin: float, full_ymax: float, dx: float
) -> tuple[float, float]:
    """Gibt ymin, ymax symmetrisch um das Domänenmittel so zurück, dass dy/dx = ASPECT."""
    dy = dx * ASPECT
    cy = (full_ymin + full_ymax) / 2
    return cy - dy / 2, cy + dy / 2

# --------------------------------------------------
# Hauptprogramm
# --------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Erstellt mehrere Wireframe‑Screenshots (Full & Zoom)")
    parser.add_argument("meshfile", help="Mesh‑Datei (.cas, .grid, .vtu, …)")
    parser.add_argument(
        "--xzoom",
        nargs=2,
        type=float,
        metavar=("XMIN", "XMAX"),
        action="append",
        help="X‑Range des Zoom‑Fensters; kann mehrfach vorkommen",
    )
    parser.add_argument("--outdir", default="imgs", help="Ausgabeverzeichnis für PNGs")

    args = parser.parse_args()

    # Standard‑Fenster, falls --xzoom fehlt (zentrales 30 %)
    xzoom_list: list[tuple[float, float]]

    obj = pv.read(args.meshfile)
    mesh = obj.combine() if isinstance(obj, pv.MultiBlock) else obj

    full_bounds = mesh.bounds  # xmin, xmax, ymin, ymax, zmin, zmax
    full_dx = full_bounds[1] - full_bounds[0]
    full_dy = full_bounds[3] - full_bounds[2]

    if args.xzoom:
        xzoom_list = [tuple(map(float, xz)) for xz in args.xzoom]
    else:
        # 30‑%‑Fenster mittig, Aspect garantiert
        xmin = full_bounds[0] + 0.35 * full_dx
        xmax = full_bounds[1] - 0.35 * full_dx
        xzoom_list = [(xmin, xmax)]

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for i, (xmin, xmax) in enumerate(xzoom_list, 1):
        dx = xmax - xmin
        ymin, ymax = symmetric_y_for_aspect(full_bounds[2], full_bounds[3], dx)
        zmin, zmax = full_bounds[4], full_bounds[5]
        zoom_bounds = (xmin, xmax, ymin, ymax, zmin, zmax)

        # Zoom‑Mesh erzeugen
        mesh_zoom = mesh.clip_box(zoom_bounds, invert=False)

        # Dateinamen
        file_full = outdir / f"wireframe_full_{i}.png"
        file_zoom = outdir / f"wireframe_zoom_{i}.png"

        # Screenshots
        screenshot_wireframe(
            mesh, full_bounds, file_full, highlight_bounds=zoom_bounds
        )
        screenshot_wireframe(mesh_zoom, zoom_bounds, file_zoom)

    print("Fertig! Bilder unter", outdir.resolve())

# --------------------------------------------------

if __name__ == "__main__":
    main()
