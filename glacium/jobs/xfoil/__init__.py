from .refine import XfoilRefineJob
from .thicken_te import XfoilThickenTEJob
from .boundary_layer import XfoilBoundaryLayerJob
from .polars import XfoilPolarsJob
from .suction_curve import XfoilSuctionCurveJob
from .convert import XfoilConvertJob

__all__ = [
    "XfoilRefineJob",
    "XfoilThickenTEJob",
    "XfoilBoundaryLayerJob",
    "XfoilPolarsJob",
    "XfoilSuctionCurveJob",
    "XfoilConvertJob",
]
