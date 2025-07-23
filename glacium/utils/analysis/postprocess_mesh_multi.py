#!/usr/bin/env python3
"""Create multiple wireframe and zoom screenshots from a mesh.

For each zoom window two PNG images are produced:

1. ``wireframe_full_<n>.png`` – full mesh with a red rectangle around the
   ``n``-th zoom region.
2. ``wireframe_zoom_<n>.png`` – zoomed view using identical camera settings.

Examples
--------
Fixed example with three windows::

    python wireframe_zoom_multi.py mesh.cas --outdir imgs

Generic usage::

    python wireframe_zoom_multi.py mesh.cas \n        --xzoom -0.05 0.05 \n        --xzoom -0.4 0.5 \n        --xzoom -0.1 0.5 \n        --outdir imgs

Each ``--xzoom xmin xmax`` automatically selects a symmetric ``y`` range so the
window has an aspect ratio of 4:3 (1600×1200). Works with ``.cas``, ``.grid``
and ``.vtu`` files; ``MultiBlock`` meshes are combined automatically.

Requires ``pyvista>=0.41`` and ``numpy`` (bundled with PyVista)."""

from __future__ import annotations
import argparse
from pathlib import Path
import pyvista as pv

WINDOW_SIZE = (1600, 1200)  # 4:3
ASPECT = WINDOW_SIZE[1] / WINDOW_SIZE[0]  # 0.75

# --------------------------------------------------
# camera – top-down (Z-axis up)
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
    """Create a wireframe screenshot with an optional red rectangle."""

    if mesh.n_cells == 0:
        print(f"⚠  {outfile.name}: mesh contains no cells – skipped")
        return

    p = pv.Plotter(off_screen=True, window_size=WINDOW_SIZE)
    p.background_color = "white"

    # render edges as tubes for better visibility
    edges = mesh.extract_all_edges()
    p.add_mesh(edges, color="black", line_width=1, render_lines_as_tubes=True)

    # optional highlight box
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
    parser = argparse.ArgumentParser(description="Create multiple wireframe screenshots (full and zoom)")
    parser.add_argument("meshfile", help="Mesh file (.cas, .grid, .vtu, …)")
    parser.add_argument(
        "--xzoom",
        nargs=2,
        type=float,
        metavar=("XMIN", "XMAX"),
        action="append",
        help="X-range of the zoom window; can be given multiple times",
    )
    parser.add_argument("--outdir", default="imgs", help="Output directory for PNGs")

    args = parser.parse_args()

    # default window if --xzoom is missing (central 30 %)
    xzoom_list: list[tuple[float, float]]

    obj = pv.read(args.meshfile)
    mesh = obj.combine() if isinstance(obj, pv.MultiBlock) else obj

    full_bounds = mesh.bounds  # xmin, xmax, ymin, ymax, zmin, zmax
    full_dx = full_bounds[1] - full_bounds[0]
    full_dy = full_bounds[3] - full_bounds[2]

    if args.xzoom:
        xzoom_list = [tuple(map(float, xz)) for xz in args.xzoom]
    else:
        # central 30 % window, aspect guaranteed
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

    print("Done! Images saved in", outdir.resolve())

# --------------------------------------------------

if __name__ == "__main__":
    main()
