from __future__ import annotations

from pathlib import Path
from glacium.engines.xfoil_base import XfoilScriptJob


class XfoilPolarsJob(XfoilScriptJob):
    """Run a polar computation."""

    name = "XFOIL_POLAR"
    template = Path("XFOIL.polars.in.j2")
    outfile = "polars.dat"
    deps = ("XFOIL_THICKEN_TE",)
