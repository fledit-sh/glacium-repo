"""Job implementations used by Glacium."""
from __future__ import annotations

from importlib import import_module

__all__ = [
    "FensapRunJob",
    "Drop3dRunJob",
    "Ice3dRunJob",
    "MultiShotRunJob",
    "Fluent2FensapJob",
    "ConvergenceStatsJob",
    "FensapConvergenceStatsJob",
    "Drop3dConvergenceStatsJob",
    "Ice3dConvergenceStatsJob",
    "AnalyzeMultishotJob",
    "FensapAnalysisJob",
    "MeshAnalysisJob",
    "PointwiseGCIJob",
    "PointwiseMesh2Job",
    "XfoilRefineJob",
    "XfoilThickenTEJob",
    "XfoilBoundaryLayerJob",
    "XfoilPolarsJob",
    "XfoilSuctionCurveJob",
    "XfoilConvertJob",
    "HelloJob",
    "PostprocessSingleFensapJob",
    "PostprocessMultishotJob",
]

_module_map = {
    "FensapRunJob": "glacium.jobs.fensap.fensap_run",
    "Drop3dRunJob": "glacium.jobs.fensap.drop3d_run",
    "Ice3dRunJob": "glacium.jobs.fensap.ice3d_run",
    "MultiShotRunJob": "glacium.jobs.fensap.multishot_run",
    "Fluent2FensapJob": "glacium.jobs.fensap.fluent2fensap",
    "ConvergenceStatsJob": "glacium.jobs.analysis.convergence_stats",
    "FensapConvergenceStatsJob": "glacium.jobs.analysis.fensap_convergence_stats",
    "Drop3dConvergenceStatsJob": "glacium.jobs.analysis.drop3d_convergence_stats",
    "Ice3dConvergenceStatsJob": "glacium.jobs.analysis.ice3d_convergence_stats",
    "AnalyzeMultishotJob": "glacium.jobs.analysis.analyze_multishot",
    "FensapAnalysisJob": "glacium.jobs.analysis.fensap_analysis",
    "MeshAnalysisJob": "glacium.jobs.analysis.mesh_analysis",
    "PointwiseGCIJob": "glacium.jobs.pointwise.gci",
    "PointwiseMesh2Job": "glacium.jobs.pointwise.mesh2",
    "XfoilRefineJob": "glacium.jobs.xfoil.refine",
    "XfoilThickenTEJob": "glacium.jobs.xfoil.thicken_te",
    "XfoilBoundaryLayerJob": "glacium.jobs.xfoil.boundary_layer",
    "XfoilPolarsJob": "glacium.jobs.xfoil.polars",
    "XfoilSuctionCurveJob": "glacium.jobs.xfoil.suction_curve",
    "XfoilConvertJob": "glacium.jobs.xfoil.convert",
    "HelloJob": "glacium.recipes.hello_world",
    "PostprocessSingleFensapJob": "glacium.jobs.postprocess.single_fensap",
    "PostprocessMultishotJob": "glacium.jobs.postprocess.multishot",
}


def __getattr__(name: str):
    if name in _module_map:
        module = import_module(_module_map[name])
        return getattr(module, name)
    raise AttributeError(name)
