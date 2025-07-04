"""Recipe preparing meshes and conversions before solver runs."""

from glacium.managers.recipe_manager import RecipeManager, BaseRecipe
from glacium.utils.JobIndex import JobFactory


@RecipeManager.register
class PrepRecipe(BaseRecipe):
    """Run the standard preparation workflow."""

    name = "prep"
    description = "Refine profile and generate initial mesh"

    def build(self, project):
        return [
            JobFactory.create("XFOIL_REFINE", project),
            JobFactory.create("XFOIL_THICKEN_TE", project),
            JobFactory.create("XFOIL_PW_CONVERT", project),
            JobFactory.create("POINTWISE_GCI", project),
            JobFactory.create("FLUENT2FENSAP", project),
        ]
