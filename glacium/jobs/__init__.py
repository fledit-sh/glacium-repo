"""Job implementations used by Glacium."""

from .fensap_jobs import (
    FensapRunJob,
    Drop3dRunJob,
    Ice3dRunJob,
    MultiShotRunJob,
)
from .analysis_jobs import (
    ConvergenceStatsJob,
    FensapConvergenceStatsJob,
    Drop3dConvergenceStatsJob,
    Ice3dConvergenceStatsJob,
)
from .pointwise_jobs import PointwiseGCIJob, PointwiseMesh2Job
from .xfoil_jobs import (
    XfoilRefineJob,
    XfoilThickenTEJob,
    XfoilBoundaryLayerJob,
    XfoilPolarsJob,
    XfoilSuctionCurveJob,
)
from glacium.engines.fluent2fensap import Fluent2FensapJob
from glacium.engines.xfoil_convert_job import XfoilConvertJob
from glacium.recipes.hello_world import HelloJob

__all__ = [
    "FensapRunJob",
    "Drop3dRunJob",
    "Ice3dRunJob",
    "MultiShotRunJob",
    "ConvergenceStatsJob",
    "FensapConvergenceStatsJob",
    "Drop3dConvergenceStatsJob",
    "Ice3dConvergenceStatsJob",
    "PointwiseGCIJob",
    "PointwiseMesh2Job",
    "XfoilRefineJob",
    "XfoilThickenTEJob",
    "XfoilBoundaryLayerJob",
    "XfoilPolarsJob",
    "XfoilSuctionCurveJob",
    "Fluent2FensapJob",
    "XfoilConvertJob",
    "HelloJob",
]
