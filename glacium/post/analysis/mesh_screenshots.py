from __future__ import annotations

import argparse
from pathlib import Path
import pyvista as pv

WINDOW_SIZE = (1600, 1200)  # 4:3
ASPECT = WINDOW_SIZE[1] / WINDOW_SIZE[0]
DEFAULT_X_RANGES = [(-0.05, 0.05), (-0.4, 0.5), (-0.1, 0.5)]


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


def screenshot_wireframe(
    mesh: pv.DataSet,
    bounds: tuple[float, float, float, float, float, float],
    outfile: Path,
    highlight_bounds: tuple[float, float, float, float, float, float] | None = None,
) -> None:
    """Create a wireframe screenshot optionally highlighting a region."""
    if mesh.n_cells == 0:
        print(f"⚠ {outfile.name}: mesh contains no cells – skipped")
        return

    p = pv.Plotter(off_screen=True, window_size=WINDOW_SIZE)
    p.background_color = "white"

    edges = mesh.extract_all_edges()
    p.add_mesh(edges, color="black", line_width=1, render_lines_as_tubes=True)

    if highlight_bounds is not None:
        box = pv.Box(bounds=highlight_bounds)
        p.add_mesh(box, color="red", style="wireframe", line_width=3, render_lines_as_tubes=True)

    p.camera = make_topdown(bounds)
    p.show(screenshot=str(outfile))
    p.close()
    print(f"✔ {outfile.name} saved")


def symmetric_y_for_aspect(
    full_ymin: float, full_ymax: float, dx: float
) -> tuple[float, float]:
    dy = dx * ASPECT
    cy = (full_ymin + full_ymax) / 2
    return cy - dy / 2, cy + dy / 2


def generate_wireframes(
    meshfile: Path,
    chord: float | None,
    out_dir: Path,
    prefix: str = "mesh",
) -> None:
    """Generate full and zoomed wireframe screenshots for a mesh."""
    obj = pv.read(meshfile)
    mesh = obj.combine() if isinstance(obj, pv.MultiBlock) else obj

    full_bounds = mesh.bounds
    if chord is not None:
        x_ranges = [(xmin * chord, xmax * chord) for xmin, xmax in DEFAULT_X_RANGES]
    else:
        x_ranges = DEFAULT_X_RANGES

    out_dir.mkdir(parents=True, exist_ok=True)

    for i, (xmin, xmax) in enumerate(x_ranges, 1):
        dx = xmax - xmin
        ymin, ymax = symmetric_y_for_aspect(full_bounds[2], full_bounds[3], dx)
        zmin, zmax = full_bounds[4], full_bounds[5]
        zoom_bounds = (xmin, xmax, ymin, ymax, zmin, zmax)

        mesh_zoom = mesh.clip_box(zoom_bounds, invert=False)

        file_full = out_dir / f"{prefix}_full_{i}.png"
        file_zoom = out_dir / f"{prefix}_zoom_{i}.png"

        screenshot_wireframe(mesh, full_bounds, file_full, highlight_bounds=zoom_bounds)
        screenshot_wireframe(mesh_zoom, zoom_bounds, file_zoom)

    print(f"Images saved to {out_dir.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create wireframe screenshots for a mesh (full and zoom views)."
    )
    parser.add_argument("meshfile", type=Path, help="Mesh file (.cas, .grid, .vtu, …)")
    parser.add_argument(
        "--chord",
        type=float,
        default=None,
        help="Reference chord length to scale default zoom windows",
    )
    parser.add_argument(
        "--out-dir", type=Path, default=Path("imgs"), help="Output directory for PNGs"
    )
    parser.add_argument(
        "--prefix", default="mesh", help="Filename prefix for generated images"
    )
    args = parser.parse_args()

    generate_wireframes(args.meshfile, args.chord, args.out_dir, prefix=args.prefix)


if __name__ == "__main__":
    main()
