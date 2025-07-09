"""Predefined Pointwise job classes."""

from pathlib import Path
from glacium.engines.pointwise import PointwiseScriptJob

class PointwiseGCIJob(PointwiseScriptJob):
    """Run the GCI grid script."""

    name = "POINTWISE_GCI"
    template = Path("POINTWISE.GCI.glf.j2")
    deps: tuple[str, ...] = ("XFOIL_THICKEN_TE",)

class PointwiseMesh2Job(PointwiseScriptJob):
    """Generate a second grid based on the GCI step."""

    name = "POINTWISE_MESH2"
    template = Path("POINTWISE.mesh2.glf.j2")
    deps = ()


