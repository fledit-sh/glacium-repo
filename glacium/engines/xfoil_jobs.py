"""Concrete job definitions for running XFOIL scripts."""

from pathlib import Path
from glacium.engines.xfoil_base import XfoilScriptJob

class XfoilRefineJob(XfoilScriptJob):
    """Refine the airfoil point distribution."""

    name = "XFOIL_REFINE"
    template = Path("XFOIL.increasepoints.in.j2")
    outfile = "refined.dat"
    deps: tuple[str, ...] = ()

class XfoilThickenTEJob(XfoilScriptJob):
    """Apply trailing edge thickening."""

    name = "XFOIL_THICKEN_TE"
    template = Path("XFOIL.thickenTE.in.j2")
    outfile = "thick.dat"
    deps = ("XFOIL_REFINE",)

class XfoilBoundaryLayerJob(XfoilScriptJob):
    """Generate a boundary layer profile."""

    name = "XFOIL_BOUNDARY"
    template = Path("XFOIL.boundarylayer.in.j2")
    outfile = "bnd.dat"
    deps = ("XFOIL_THICKEN_TE",)

class XfoilPolarsJob(XfoilScriptJob):
    """Run a polar computation."""

    name = "XFOIL_POLAR"
    template = Path("XFOIL.polars.in.j2")
    outfile = "polars.dat"
    deps = ("XFOIL_THICKEN_TE",)

class XfoilSuctionCurveJob(XfoilScriptJob):
    """Create a suction distribution curve."""

    name = "XFOIL_SUCTION"
    template = Path("XFOIL.suctioncurve.in.j2")
    outfile = "psi.dat"
    deps = ("XFOIL_THICKEN_TE",)

