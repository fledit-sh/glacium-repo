from __future__ import annotations

from pathlib import Path
from glacium.engines.xfoil_base import XfoilScriptJob


class XfoilBoundaryLayerJob(XfoilScriptJob):
    """Generate a boundary layer profile."""

    name = "XFOIL_BOUNDARY"
    template = Path("XFOIL.boundarylayer.in.j2")
    outfile = "bnd.dat"
    deps = ("XFOIL_THICKEN_TE",)
