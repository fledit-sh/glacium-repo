from __future__ import annotations

import pyvista as pv


def make_topdown(bounds: tuple[float, float, float, float, float, float]) -> pv.Camera:
    """Return a parallel top‑down camera for the given bounds."""
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
