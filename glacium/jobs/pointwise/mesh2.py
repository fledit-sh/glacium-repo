from __future__ import annotations

from pathlib import Path
from glacium.engines.pointwise import PointwiseScriptJob


class PointwiseMesh2Job(PointwiseScriptJob):
    """Generate a second grid based on the GCI step."""

    name = "POINTWISE_MESH2"
    template = Path("POINTWISE.mesh2.glf.j2")
    deps = ()
