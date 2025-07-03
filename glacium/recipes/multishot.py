"""Recipes providing standard XFOIL workflows."""

from glacium.managers.recipe_manager import RecipeManager, BaseRecipe

from glacium.engines.xfoil_convert_job import XfoilConvertJob
from glacium.jobs.xfoil_jobs import (
    XfoilRefineJob,
    XfoilThickenTEJob,
)
from glacium.jobs.pointwise_jobs import PointwiseGCIJob
from glacium.engines.fluent2fensap import Fluent2FensapJob
from glacium.jobs.fensap_jobs import MultiShotRunJob

@RecipeManager.register
class DefaultAero(BaseRecipe):
    """Full multishot recipe."""

    name = "multishot"
    description = "Kompletter XFOIL-Workflow"

    def build(self, project):
        return [
            XfoilRefineJob(project),
            XfoilThickenTEJob(project),
            XfoilConvertJob(project),
            PointwiseGCIJob(project),
            Fluent2FensapJob(project),
            MultiShotRunJob(project),
        ]

