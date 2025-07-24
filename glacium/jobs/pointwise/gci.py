from __future__ import annotations

from pathlib import Path
from glacium.engines.pointwise import PointwiseScriptJob


class PointwiseGCIJob(PointwiseScriptJob):
    """Run the GCI grid script."""

    name = "POINTWISE_GCI"
    template = Path("POINTWISE.GCI.glf.j2")
    deps: tuple[str, ...] = ("XFOIL_THICKEN_TE",)
