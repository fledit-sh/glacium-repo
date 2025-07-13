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
]
