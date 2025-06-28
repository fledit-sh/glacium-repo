# glacium/engines/xfoil_jobs.py
from pathlib import Path
from glacium.engines.XfoilBase import XfoilScriptJob

class XfoilRefineJob(XfoilScriptJob):
    name      = "XFOIL_REFINE"
    template  = Path("XFOIL.increasepoints.in.j2")
    outfile   = "refined.dat"
    deps      = ()

class XfoilThickenTEJob(XfoilScriptJob):
    name      = "XFOIL_THICKEN_TE"
    template  = Path("XFOIL.thickenTE.in.j2")
    outfile   = "thick.dat"
    deps      = ("XFOIL_REFINE",)

class XfoilBoundaryLayerJob(XfoilScriptJob):
    name      = "XFOIL_BOUNDARY"
    template  = Path("XFOIL.boundarylayer.in.j2")
    outfile   = "bnd.dat"
    deps      = ("XFOIL_THICKEN_TE",)

class XfoilPolarsJob(XfoilScriptJob):
    name      = "XFOIL_POLAR"
    template  = Path("XFOIL.polars.in.j2")
    outfile   = "polars.dat"
    deps      = ("XFOIL_THICKEN_TE",)

class XfoilSuctionCurveJob(XfoilScriptJob):
    name      = "XFOIL_SUCTION"
    template  = Path("XFOIL.suctioncurve.in.j2")
    outfile   = "psi.dat"
    deps      = ("XFOIL_THICKEN_TE",)
