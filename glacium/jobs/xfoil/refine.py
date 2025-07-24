from __future__ import annotations

from pathlib import Path
from glacium.engines.xfoil_base import XfoilScriptJob


class XfoilRefineJob(XfoilScriptJob):
    """Refine the airfoil point distribution."""

    name = "XFOIL_REFINE"
    template = Path("XFOIL.increasepoints.in.j2")
    outfile = "refined.dat"
    deps: tuple[str, ...] = ()
