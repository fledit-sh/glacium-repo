"""Recipes providing standard XFOIL workflows."""

from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
from glacium.engines.configurator import ReynoldsConfigJob
from glacium.engines.xfoil_jobs import (
    XfoilRefineJob,
    XfoilThickenTEJob,
    XfoilBoundaryLayerJob,
    XfoilPolarsJob,
    XfoilSuctionCurveJob,
)
from glacium.engines.xfoil_convert_job import XfoilConvertJob
from glacium.engines.fensap import FensapRunJob
from glacium.engines.pointwise_jobs import PointwiseGCIJob


@RecipeManager.register
class DefaultAero(BaseRecipe):
    """Full XFOIL workflow recipe."""

    name = "default_aero"
    description = "Kompletter XFOIL-Workflow"

    def build(self, project):
        return [
            ReynoldsConfigJob(project),
            XfoilRefineJob(project),
            XfoilThickenTEJob(project),
            XfoilConvertJob(project),
            XfoilBoundaryLayerJob(project),
            XfoilPolarsJob(project),
            XfoilSuctionCurveJob(project),
        ]

@RecipeManager.register
class MinimalXfoil(BaseRecipe):
    """Minimal variant containing only the refine and thicken jobs."""

    name = "minimal_xfoil"
    description = "Minimaler XFOIL-Workflow"

    def build(self, project):
        return [
            ReynoldsConfigJob(project),
            XfoilRefineJob(project),
            XfoilThickenTEJob(project),
            XfoilConvertJob(project),
            PointwiseGCIJob(project),
            FensapRunJob(project),
        ]
