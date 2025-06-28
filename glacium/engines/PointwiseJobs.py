from pathlib import Path
from glacium.engines.pointwise import PointwiseScriptJob

class PointwiseGCIJob(PointwiseScriptJob):
    name     = "POINTWISE_GCI"
    template = Path("POINTWISE.GCI.glf.j2")
    deps     = ()

class PointwiseMesh2Job(PointwiseScriptJob):
    name     = "POINTWISE_MESH2"
    template = Path("POINTWISE.mesh2.glf.j2")
    deps     = ("POINTWISE_GCI",)

