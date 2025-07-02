"""Recipes providing standard XFOIL workflows."""

from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
from glacium.jobs.xfoil_jobs import (
    XfoilRefineJob,
    XfoilThickenTEJob,
    XfoilBoundaryLayerJob,
    XfoilPolarsJob,
    XfoilSuctionCurveJob,
)
from glacium.engines.xfoil_convert_job import XfoilConvertJob
from glacium.jobs.pointwise_jobs import PointwiseGCIJob
from glacium.engines.fluent2fensap import Fluent2FensapJob


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
            PointwiseGCIJob(project),
            Fluent2FensapJob(project),
        ]

