from __future__ import annotations

from pathlib import Path
from glacium.engines.xfoil_base import XfoilScriptJob


class XfoilSuctionCurveJob(XfoilScriptJob):
    """Create a suction distribution curve."""

    name = "XFOIL_SUCTION"
    template = Path("XFOIL.suctioncurve.in.j2")
    outfile = "psi.dat"
    deps = ("XFOIL_THICKEN_TE",)
