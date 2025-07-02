"""Recipes providing standard XFOIL workflows."""

from glacium.engines.fensap import FensapRunJob
from glacium.engines.PointwiseJobs import PointwiseGCIJob
from glacium.engines.XfoilConvertJob import XfoilConvertJob
from glacium.engines.XfoilJobs import (
    XfoilBoundaryLayerJob,
    XfoilPolarsJob,
    XfoilRefineJob,
    XfoilSuctionCurveJob,
    XfoilThickenTEJob,
)
from glacium.managers.RecipeManager import BaseRecipe, RecipeManager


@RecipeManager.register
class DefaultAero(BaseRecipe):
    """Full XFOIL workflow recipe."""

    name = "default_aero"
    description = "Kompletter XFOIL-Workflow"

    def build(self, project):
        return [
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
            XfoilRefineJob(project),
            XfoilThickenTEJob(project),
            XfoilConvertJob(project),
            PointwiseGCIJob(project),
            FensapRunJob(project),
        ]
