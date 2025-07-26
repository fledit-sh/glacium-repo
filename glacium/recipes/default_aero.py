"""Recipes providing standard XFOIL workflows."""

from glacium.managers.recipe_manager import RecipeManager, BaseRecipe
from glacium.utils.job_index import JobFactory
from glacium.engines.pointwise import PointwiseEngine


@RecipeManager.register
class DefaultAero(BaseRecipe):
    """Full XFOIL workflow recipe."""

    name = "default_aero"
    description = "Kompletter XFOIL-Workflow"

    def build(self, project):
        return [
            JobFactory.create("XFOIL_REFINE", project),
            JobFactory.create("XFOIL_THICKEN_TE", project),
            JobFactory.create("XFOIL_PW_CONVERT", project),
            JobFactory.create("POINTWISE_GCI", project, engine=PointwiseEngine),
            JobFactory.create("FLUENT2FENSAP", project),
        ]

