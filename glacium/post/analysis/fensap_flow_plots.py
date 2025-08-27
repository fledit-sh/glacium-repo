# teccy.py — PyVista-Screenshot -> Matplotlib mit Achsen
import argparse
from pathlib import Path
from typing import Sequence
import re
import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpatches
import tempfile
import os
import scienceplots
plt.style.use(["science","no-latex"])

__all__ = ["fensap_flow_plots"]

# ---------- Einstellungen ----------
SIZES = [("full", (6.3, 3.9), 0.15), ("dbl", (3.15, 2.0), 0.25)]  # (Label, figsize, cbar_pad)
pv.global_theme.show_scalar_bar = False               # PyVista-Colorbar global aus

# Viewport definitions. Ranges starting at -0.1 will later be adjusted to a
# configured minimum x/c value via :func:`build_views`.
BASE_VIEWS = [
    ((-0.1, 0.1), 0.0),
    ((0.9, 1.1), 0.0),
    ((-0.1, 0.5), 0.0),
    ((-0.1, 1.1), 0.0),
    ((-1.0, 2.0), 0.0),
]

# Minimum x/c positions used to build a fixed set of viewports.
MIN_XC_VALUES = [-0.2, -0.1, -0.3, -0.4, -0.5]


def build_views(min_xc: float):
    """Build viewport tuples adjusting ranges starting at ``-0.1``.

    Parameters
    ----------
    min_xc:
        The minimum x/c value used to build the viewport set.

    Returns
    -------
    list
        A list of ``(x_range, y_center, tag)`` tuples where the tag encodes the
        viewport range. Any base range beginning at ``-0.1`` is replaced by
        ``min_xc``.
    """

    views = []
    for (xmin, xmax), yc in BASE_VIEWS:
        if np.isclose(xmin, -0.1):
            xmin = min_xc
        tag = f"xc_{xmin}_{xmax}_yc_{yc}"
        views.append(((xmin, xmax), yc, tag))
    return views

# ---------- Utils ----------
def sanitize(name: str) -> str:
    return re.sub(r'[^0-9a-zA-Z_.-]+', '_', name).strip('_')

def ensure_outdir(d: Path) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    return d


def rectangles_from_views(views, overview_tag):
    """Create rectangle definitions for all views except the overview."""

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
    """
    Orthografische Top-Down-Kamera (VTK: parallel_scale = halbe Höhe).
    Liefert xlim, ylim für Matplotlib.
    """
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

def pyvista_render_and_shoot(slc, vname, xrng, ycenter, window=(1600,1200), cmap="plasma"):
    """
    Rendert Slice mit PyVista (ohne PV-Scalarbar) und liefert:
    xlim, ylim, (vmin,vmax), tmp_png, cmap_name
    """
    arr = slc.point_data[vname]
    vmin, vmax = float(np.nanmin(arr)), float(np.nanmax(arr))

    p = pv.Plotter(off_screen=True, window_size=window)
    p.set_background("white")

    p.add_mesh(
        slc,
        scalars=vname,
        cmap=cmap,
        clim=(vmin, vmax),
        point_size=3,
        lighting=False,
        render_points_as_spheres=False,
        nan_color="white",
        nan_opacity=0.0,
        show_scalar_bar=False,  # sicher aus
    )
    # Fallback: restliche Bars entfernen (versionsabhängig)
    try:
        if hasattr(p, "remove_scalar_bars"):
            p.remove_scalar_bars()
        elif hasattr(p, "remove_scalar_bar"):
            p.remove_scalar_bar()
    except Exception:
        pass

    xlim, ylim = set_topdown_camera(p, slc.bounds, xrng, ycenter, aspect=(4,3))

    tmp_png = Path(tempfile.mkstemp(prefix="pvshot_", suffix=".png")[1])
    p.show(screenshot=str(tmp_png))
    return xlim, ylim, (vmin, vmax), tmp_png, cmap

def _composite_rgba_over_white(img):
    """PNG mit Alpha gegen weißen Hintergrund kompositen."""
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
    """
    Zeichnet rote Rechtecke & Nummern für gegebene Boxen (Liste aus (xmin,xmax,ymin,ymax, label)).
    Nummern werden automatisch vergeben.
    """
    k = number_start
    for (xmin, xmax, ymin, ymax, lbl) in boxes:
        # nur zeichnen, wenn Kasten innerhalb des großen Sichtfensters liegt
        if xmax < xlim[0] or xmin > xlim[1] or ymax < ylim[0] or ymin > ylim[1]:
            continue
        rect = mpatches.Rectangle((xmin, ymin), xmax-xmin, ymax-ymin,
                                  fill=False, edgecolor='red', linewidth=1.5, alpha=0.9)
        ax.add_patch(rect)
        # Nummer links-oben (kleiner Versatz)
        tx = xmin - 0.04*(xlim[1]-xlim[0])
        ty = ymax - 0.02*(ylim[1]-ylim[0])
        ax.text(tx, ty, f"{k}", color='red', fontsize=10, weight='bold',
                ha='left', va='top',
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="red", lw=0.8, alpha=0.8))
        k += 1

def overlay_axes_on_screenshot(
    screenshot_png, xlim, ylim, clim, cmap_name, label, out_png, figsize,
    rectangles=None, dpi=300, cbar_pad=0.15
):
    """
    Matplotlib-Overlay: Achsen + Colorbar, optional rote Rechtecke/Nummern (rectangles).
    """
    img = mpimg.imread(str(screenshot_png))
    img_rgb = _composite_rgba_over_white(img)

    fig, ax = plt.subplots(figsize=figsize)  # 4:3-ähnlich durch Kamera, hier frei
    ax.set_facecolor("white")
    ax.imshow(
        img_rgb,
        extent=[xlim[0], xlim[1], ylim[0], ylim[1]],
        origin="upper",
        interpolation="nearest",
        aspect="auto",
        zorder=0,
    )

    # Rechtecke einzeichnen (für Überblicksbild)
    if rectangles:
        draw_viewport_rects(ax, rectangles, xlim, ylim, number_start=1)

    # Achsenformatierung
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_aspect("equal", "box")
    ax.set_xlabel("x/c"); ax.set_ylabel("y/c")
    ax.minorticks_on()
    ax.tick_params(which="both", direction="out", length=6, width=1)
    ax.tick_params(which="minor", length=3, width=0.8)

    # Colorbar außerhalb
    import matplotlib as mpl
    sm = mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=clim[0], vmax=clim[1]),
                               cmap=plt.get_cmap(cmap_name))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.06, pad=cbar_pad)
    cbar.set_label(label)
    cbar.ax.set_facecolor("white")
    if getattr(cbar, "outline", None) is not None:
        cbar.outline.set_edgecolor("black")
        cbar.outline.set_linewidth(0.8)

    fig.tight_layout()
    fig.savefig(str(out_png), dpi=dpi)
    plt.close(fig)

# ---------- Main ----------
def main(argv: Sequence[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path, help="Tecplot .dat")
    ap.add_argument("outdir", nargs="?", type=Path, help="Output directory")
    ap.add_argument("--scale", type=float, default=1.0, help="Teile X,Y durch diesen Wert (z.B. 0.431)")
    ap.add_argument("--cmap", default="plasma")
    ap.add_argument("-o","--outdir", dest="outdir_opt", type=Path, help="Output directory")
    args = ap.parse_args(argv)

    outdir = args.outdir_opt or args.outdir or Path("out_axes")
    ensure_outdir(outdir)

    # Tecplot laden
    reader = pv.TecplotReader(str(args.file))
    mesh = reader.read()
    grid = mesh[0] if isinstance(mesh, pv.MultiBlock) else mesh

    # Skalierung x,y -> x/c,y/c
    if args.scale != 1.0:
        pts = grid.points.copy()
        pts[:,:2] /= args.scale
        grid.points = pts

    # XY-Slice
    slc = grid.slice(normal="z")

    variables = []
    for vname in slc.point_data.keys():
        arr = slc.point_data[vname]
        if not isinstance(arr, np.ndarray) or arr.dtype.kind not in "fc":
            continue
        if not np.isfinite(arr).any():
            continue
        if np.isclose(np.nanmin(arr), np.nanmax(arr)):
            continue
        variables.append(vname)

    def process(base: float, suffix: str | None = None):
        """Render all views for a given minimum x/c value.

        Parameters
        ----------
        base:
            Minimum x/c used to adjust view ranges starting at ``-0.1``.
        suffix:
            Optional directory suffix to keep outputs separated per value.
        """

        views = build_views(base)
        overview_tag = views[-1][2]
        rects = rectangles_from_views(views, overview_tag)

        for vname in variables:
            vdir_base = outdir / sanitize(vname)
            if suffix:
                vdir_base = vdir_base / suffix
            vdir = ensure_outdir(vdir_base)

            for (xrng, ycenter, tag) in views:
                xlim, ylim, clim, tmp_png, cmap_name = pyvista_render_and_shoot(
                    slc, vname, xrng, ycenter, cmap=args.cmap
                )

                rectangles = rects if tag == overview_tag else None

                for label, figsize, cbar_pad in SIZES:
                    out_png = vdir / f"{sanitize(vname)}__{tag}__{label}.png"
                    overlay_axes_on_screenshot(
                        tmp_png, xlim, ylim, clim, cmap_name, vname, out_png,
                        figsize=figsize, rectangles=rectangles, cbar_pad=cbar_pad
                    )

                try:
                    os.remove(tmp_png)
                except OSError:
                    pass

                print(
                    f"✔ {sanitize(vname)} — {tag} — saved {', '.join(l for l,_,_ in SIZES)}"
                )

    # Build views for each configured minimum x/c value
    for base in MIN_XC_VALUES:
        process(base, suffix=f"min_xc_{sanitize(str(base))}")


def fensap_flow_plots(cwd: Path, args: Sequence[str | Path]) -> None:
    """Run slice plotting for FENSAP results.

    Viewports are built for each configured minimum x/c value from
    :data:`MIN_XC_VALUES` and rendered accordingly.

    Parameters
    ----------
    cwd:
        Working directory supplied by :class:`~glacium.engines.py_engine.PyEngine`.
        Unused but kept for API compatibility.
    args:
        Sequence containing command line style arguments. The first argument is
        the Tecplot file path, followed optionally by an output directory,
        ``--scale`` and ``--cmap`` options.
    """
    main([str(a) for a in args])


if __name__ == "__main__":
    main()
