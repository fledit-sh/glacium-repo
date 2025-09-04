# mesh_viewports.py — Mesh-Wireframe-Screenshots mit Achsen & festen Viewports
import argparse
import os
import re
import tempfile
from pathlib import Path
from typing import Sequence

import matplotlib.image as mpimg
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
import scienceplots
plt.style.use(["science","no-latex"])

__all__ = ["fensap_mesh_plots"]

# ---------- Einstellungen ----------
SIZES = [("full", (6.3, 3.9), 0.15), ("dbl", (3.15, 2.0), 0.4)]
pv.global_theme.show_scalar_bar = False

BASE_VIEWS = [
    ((-0.1, 0.1), 0.0),
    ((0.9, 1.1), 0.0),
    ((-0.1, 0.5), 0.0),
    ((-0.1, 1.1), 0.0),
    ((-1.0, 2.0), 0.0),
]
MIN_XC_VALUES = [-0.1, -0.3, -0.5]

# ---------- Utils ----------
def build_views(min_xc: float):
    views = []
    for (xmin, xmax), yc in BASE_VIEWS:
        if np.isclose(xmin, -0.1):
            xmin = min_xc
        tag = f"xc_{xmin}_{xmax}_yc_{yc}"
        views.append(((xmin, xmax), yc, tag))
    return views

def sanitize(name: str) -> str:
    return re.sub(r'[^0-9a-zA-Z_.-]+', '_', name).strip('_')

def ensure_outdir(d: Path) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    return d

def rectangles_from_views(views, overview_tag):
    rects = []
    for (xrng, yc, tag) in views:
        if tag == overview_tag:
            continue
        xmin, xmax = xrng
        width = xmax - xmin
        height = width * (3 / 4)
        ymin = yc - 0.5 * height
        ymax = yc + 0.5 * height
        rects.append((xmin, xmax, ymin, ymax, tag))
    return rects

def set_topdown_camera(plotter: pv.Plotter, bounds, x_rng, y_center, aspect=(4, 3)):
    xmin, xmax = x_rng
    width  = xmax - xmin
    height = width * (aspect[1] / aspect[0])
    ymin = y_center - 0.5 * height
    ymax = y_center + 0.5 * height

    zmin, zmax = bounds[4], bounds[5]
    cx, cy, cz = 0.5*(xmin+xmax), 0.5*(ymin+ymax), 0.5*(zmin+zmax)

    cam = pv.Camera()
    cam.position = (cx, cy, cz + 10.0)
    cam.focal_point = (cx, cy, cz)
    cam.view_up = (0, 1, 0)
    cam.parallel_projection = True
    cam.parallel_scale = height/2.0
    plotter.camera = cam

    return (xmin, xmax), (ymin, ymax)

def pyvista_render_mesh_and_shoot(slc, xrng, ycenter, window=(3200,2400), line_width=0.6):
    """
    Rendert nur den Mesh (Wireframe) mit weißem Hintergrund und liefert:
    xlim, ylim, tmp_png
    """
    p = pv.Plotter(off_screen=True, window_size=window)
    p.enable_anti_aliasing("ssaa")  # oder "msaa"
    p.set_background("white")

    # Wenn möglich Wireframe, sonst Kanten zeigen
    p.add_mesh(
        slc,
        style="wireframe",
        color="black",
        line_width=line_width,
        show_scalar_bar=False,
        lighting=False,
    )

    # Fallback: sicherstellen, dass keine Scalarbars auftauchen
    try:
        if hasattr(p, "remove_scalar_bars"):
            p.remove_scalar_bars()
        elif hasattr(p, "remove_scalar_bar"):
            p.remove_scalar_bar()
    except Exception:
        pass

    xlim, ylim = set_topdown_camera(p, slc.bounds, xrng, ycenter, aspect=(4,3))

    tmp_png = Path(tempfile.mkstemp(prefix="pvshot_mesh_", suffix=".png")[1])
    p.show(screenshot=str(tmp_png))
    return xlim, ylim, tmp_png

def _composite_rgba_over_white(img):
    if img.ndim == 3 and img.shape[2] == 4:
        arr = img.astype(np.float32)
        if arr.max() > 1.0:
            arr /= 255.0
        rgb = arr[..., :3]
        alpha = arr[..., 3:4]
        return rgb * alpha + (1.0 - alpha)
    if img.ndim == 3 and img.shape[2] == 3:
        return img
    return np.dstack([img, img, img])

def draw_viewport_rects(ax, boxes, xlim, ylim, number_start=1):
    k = number_start
    for (xmin, xmax, ymin, ymax, lbl) in boxes:
        if xmax < xlim[0] or xmin > xlim[1] or ymax < ylim[0] or ymin > ylim[1]:
            continue
        rect = mpatches.Rectangle((xmin, ymin), xmax-xmin, ymax-ymin,
                                  fill=False, edgecolor='red', linewidth=1.5, alpha=0.9)
        ax.add_patch(rect)
        tx = xmin - 0.04*(xlim[1]-xlim[0])
        ty = ymax - 0.02*(ylim[1]-ylim[0])
        ax.text(tx, ty, f"{k}", color='red', fontsize=10, weight='bold',
                ha='left', va='top',
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="red", lw=0.8, alpha=0.8))
        k += 1

def overlay_axes_on_screenshot(
    screenshot_png, xlim, ylim, out_png, figsize, rectangles=None, dpi=300, cbar_pad=0.15
):
    """
    Matplotlib-Overlay: Achsen + optional rote Rechtecke (keine Colorbar).
    """
    img = mpimg.imread(str(screenshot_png))
    img_rgb = _composite_rgba_over_white(img)

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor("white")
    ax.imshow(
        img_rgb,
        extent=[xlim[0], xlim[1], ylim[0], ylim[1]],
        origin="upper",
        interpolation="nearest",
        aspect="auto",
        zorder=0,
    )

    if rectangles:
        draw_viewport_rects(ax, rectangles, xlim, ylim, number_start=1)

    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_aspect("equal", "box")
    ax.set_xlabel("x/c"); ax.set_ylabel("y/c")
    ax.minorticks_on()
    ax.tick_params(which="both", direction="out", length=6, width=1)
    ax.tick_params(which="minor", length=3, width=0.8)

    fig.tight_layout()
    fig.savefig(str(out_png), dpi=dpi)
    plt.close(fig)

# ---------- Main ----------
def _main(argv: Sequence[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path, help="Mesh-Datei (z. B. .dat, .cas, .vtk, .vtu, .grid)")
    ap.add_argument("outdir", nargs="?", type=Path, help="Output directory")
    ap.add_argument("--scale", type=float, default=1.0, help="Teile X,Y durch diesen Wert (z.B. 0.431) für x/c, y/c")
    ap.add_argument("--line-width", type=float, default=8, help="Linienbreite des Wireframes")
    ap.add_argument("-o","--outdir", dest="outdir_opt", type=Path, help="Output directory")
    args = ap.parse_args(argv)

    outdir = args.outdir_opt or args.outdir or Path("out_mesh")
    ensure_outdir(outdir)

    # Allgemein per PyVista lesen (statt speziell TecplotReader)
    mesh = pv.read(str(args.file))
    grid = mesh[0] if isinstance(mesh, pv.MultiBlock) else mesh

    # Skalierung x,y -> x/c,y/c
    if args.scale != 1.0:
        pts = grid.points.copy()
        pts[:,:2] /= args.scale
        grid.points = pts

    # XY-Slice (Top-Down)
    slc = grid.slice(normal="z")

    def process(base: float, suffix: str | None = None):
        views = build_views(base)
        overview_tag = views[-1][2]
        rects = rectangles_from_views(views, overview_tag)

        vdir_base = outdir / "mesh_wire"
        if suffix:
            vdir_base = vdir_base / suffix
        vdir = ensure_outdir(vdir_base)

        for (xrng, ycenter, tag) in views:
            xlim, ylim, tmp_png = pyvista_render_mesh_and_shoot(
                slc, xrng, ycenter, line_width=args.line_width
            )
            rectangles = rects if tag == overview_tag else None

            for label, figsize, cbar_pad in SIZES:
                out_png = vdir / f"mesh__{tag}__{label}.png"
                overlay_axes_on_screenshot(
                    tmp_png, xlim, ylim, out_png, figsize=figsize, rectangles=rectangles, cbar_pad=cbar_pad
                )

            try:
                os.remove(tmp_png)
            except OSError:
                pass

            print(f"✔ mesh — {tag} — saved {', '.join(l for l,_,_ in SIZES)}")

    for base in MIN_XC_VALUES:
        process(base, suffix=f"min_xc_{sanitize(str(base))}")

def fensap_mesh_plots(cwd: Path, args: Sequence[str | Path]) -> None:
    """Wie fensap_flow_plots, aber erstellt Wireframe-Mesh-Bilder in festen Viewports."""
    _main([str(a) for a in args])

if __name__ == "__main__":
    _main()
