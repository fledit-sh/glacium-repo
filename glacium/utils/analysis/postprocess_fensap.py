from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np
import pyvista as pv

"""Automatic slice plotter for Tecplot files.

The script reads a Tecplot file, creates a Z-slice and stores two images for
every point variable:

1. The entire slice with a red rectangle highlighting the zoom window.
2. The zoomed slice precisely matching the provided bounding box.

Adjust ``FILE`` and ``ZOOM_BOUNDS`` when processing different cases.
"""

__all__ = ["fensap_analysis"]


def _run(file: Path, out_dir: Path, zoom: tuple[float, float, float, float] | None = None,
         normal: str = "z") -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # load Tecplot file
    # -----------------------------
    reader = pv.TecplotReader(str(file))
    mesh = reader.read()
    grid = mesh[0] if isinstance(mesh, pv.MultiBlock) else mesh

    # -----------------------------
    # sanitize problematic names and add additional arrays
    # -----------------------------
    rename_map = {
        "V1-velocity [m_s]; Velocity": "Vx",
        "V2-velocity [m_s]": "Vy",
        "V3-velocity [m_s]": "Vz",
        "Pressure [Pa]": "p",
    }
    for old, new in rename_map.items():
        if old in grid.point_data and new not in grid.point_data:
            grid.rename_array(old, new)

    # add velocity magnitude if components are present
    if all(k in grid.point_data for k in ("Vx", "Vy", "Vz")) and "VelMag" not in grid.point_data:
        v = np.column_stack([grid["Vx"], grid["Vy"], grid["Vz"]])
        grid["VelMag"] = np.linalg.norm(v, axis=1)

    # -----------------------------
    # prepare slice and zoom window
    # -----------------------------
    slc = grid.slice(normal=normal)

    if zoom is None:
        xmin, xmax, ymin, ymax = -0.5, 0.8, -0.5, 0.5
    else:
        xmin, xmax, ymin, ymax = zoom
    zmin, zmax = slc.bounds[4], slc.bounds[5]
    zoom_bounds = (xmin, xmax, ymin, ymax, zmin, zmax)
    zoom_box = pv.Box(bounds=zoom_bounds)
    slc_zoom = slc.clip_box(zoom_bounds, invert=False)

    def make_topdown(bounds: tuple[float, float, float, float, float, float]) -> pv.Camera:
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2
        cz = (zmin + zmax) / 2
        width = xmax - xmin
        height = ymax - ymin
        cam = pv.Camera()
        cam.position = (cx, cy, cz + 10.0)
        cam.focal_point = (cx, cy, cz)
        cam.view_up = (0, 1, 0)
        cam.parallel_projection = True
        cam.parallel_scale = max(width, height) / 2.0
        return cam

    def plot_slice(dataset: pv.DataSet, bounds: tuple[float, float, float, float, float, float],
                   var_name: str, is_zoom: bool, cmap: str = "plasma") -> pv.Plotter:
        arr = dataset[var_name]
        vmin, vmax = float(np.nanmin(arr)), float(np.nanmax(arr))

        bar = dict(
            title=f"{var_name}",
            fmt="%.2g",
            n_labels=4,
            title_font_size=14,
            label_font_size=12,
            vertical=False,
            position_x=0.25,
            position_y=0.02,
            width=0.5,
            height=0.08,
            color="black",
        )

        p = pv.Plotter(off_screen=True, window_size=(1600, 1200))
        p.add_mesh(dataset, scalars=var_name, cmap=cmap, clim=[vmin, vmax], scalar_bar_args=bar)

        if not is_zoom:
            p.add_mesh(zoom_box, color="red", style="wireframe", line_width=4)

        p.camera = make_topdown(bounds)
        return p

    print("\n=== Available point variables ===")
    for vname in grid.point_data.keys():
        print("  •", vname)
    print()

    for var in grid.point_data.keys():
        full_plot = plot_slice(slc, slc.bounds, var, is_zoom=False)
        full_file = out_dir / f"{var}_full.png"
        full_plot.show(screenshot=str(full_file))
        print(f"✔ {full_file.name} saved")

        zoom_plot = plot_slice(slc_zoom, zoom_bounds, var, is_zoom=True)
        zoom_file = out_dir / f"{var}_zoom.png"
        zoom_plot.show(screenshot=str(zoom_file))
        print(f"✔ {zoom_file.name} saved")

    print(f"\nAll plots stored in {out_dir.resolve()}")


def fensap_analysis(cwd: Path, args: Sequence[str | Path]) -> None:
    if not args:
        raise ValueError("fensap_analysis requires a Tecplot file path")

    file = Path(args[0])
    out_dir = Path(args[1]) if len(args) > 1 else Path("analysis/FENSAP")
    zoom = tuple(map(float, args[2:6])) if len(args) >= 6 else None
    _run(file, out_dir, zoom)


def main(argv: Sequence[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Generate slice plots for a Tecplot file")
    ap.add_argument("file", help="Tecplot input file")
    ap.add_argument("-o", "--outdir", default="plots", help="Output directory")
    ap.add_argument("--zoom", nargs=4, type=float, metavar=("XMIN", "XMAX", "YMIN", "YMAX"),
                    help="XY bounds of zoom window")
    ap.add_argument("--normal", default="z", help="Slice normal axis")
    args = ap.parse_args(argv)

    _run(Path(args.file), Path(args.outdir), tuple(args.zoom) if args.zoom else None, args.normal)


if __name__ == "__main__":
    main()
