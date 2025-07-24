from __future__ import annotations

from pathlib import Path
from glacium.engines.xfoil_base import XfoilScriptJob


class XfoilThickenTEJob(XfoilScriptJob):
    """Apply trailing edge thickening."""

    name = "XFOIL_THICKEN_TE"
    template = Path("XFOIL.thickenTE.in.j2")
    outfile = "thick.dat"
    deps = ("XFOIL_REFINE",)
