"""Job implementations used by Glacium."""

from .fensap_jobs import (
    FensapRunJob,
    Drop3dRunJob,
    Ice3dRunJob,
    MultiShotRunJob,
)

__all__ = [
    "FensapRunJob",
    "Drop3dRunJob",
    "Ice3dRunJob",
    "MultiShotRunJob",
]

try:  # pragma: no cover - optional analysis dependencies
    from .analysis_jobs import (
        ConvergenceStatsJob,
        FensapConvergenceStatsJob,
        Drop3dConvergenceStatsJob,
        Ice3dConvergenceStatsJob,
        FensapAnalysisJob,
        MeshAnalysisJob,
    )

    __all__ += [
        "ConvergenceStatsJob",
        "FensapConvergenceStatsJob",
        "Drop3dConvergenceStatsJob",
        "Ice3dConvergenceStatsJob",
        "FensapAnalysisJob",
        "MeshAnalysisJob",
    ]
except Exception:  # pragma: no cover - missing optional dependencies
    pass

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

__all__ += [
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

try:  # pragma: no cover - optional post-processing dependencies
    from .postprocess_jobs import PostprocessSingleFensapJob, PostprocessMultishotJob

    __all__ += [
        "PostprocessSingleFensapJob",
        "PostprocessMultishotJob",
    ]
except Exception:  # pragma: no cover - missing optional dependencies
    pass
