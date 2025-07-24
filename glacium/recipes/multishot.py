"""Recipes providing standard XFOIL workflows."""

from glacium.managers.recipe_manager import RecipeManager, BaseRecipe
from glacium.utils.JobIndex import JobFactory
from glacium.engines.pointwise import PointwiseEngine
from glacium.engines.fensap import FensapEngine

@RecipeManager.register
class DefaultAero(BaseRecipe):
    """Full multishot recipe."""

    name = "multishot"
    description = "Kompletter XFOIL-Workflow"

    def build(self, project):
        return [
            JobFactory.create("XFOIL_REFINE", project),
            JobFactory.create("XFOIL_THICKEN_TE", project),
            JobFactory.create("XFOIL_PW_CONVERT", project),
            JobFactory.create("POINTWISE_GCI", project, engine=PointwiseEngine),
            JobFactory.create("FLUENT2FENSAP", project),
            JobFactory.create("MULTISHOT_RUN", project, engine=FensapEngine),
            JobFactory.create("CONVERGENCE_STATS", project),
        ]

