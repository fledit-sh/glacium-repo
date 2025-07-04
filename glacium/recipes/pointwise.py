"""Recipe integrating Pointwise mesh generation jobs."""

from glacium.managers.recipe_manager import RecipeManager, BaseRecipe
from glacium.utils.JobIndex import JobFactory

@RecipeManager.register
class PointwiseRecipe(BaseRecipe):
    """Run the Pointwise GCI and mesh generation scripts."""

    name = "pointwise"
    description = "Run Pointwise mesh scripts"

    def build(self, project):
        return [
            JobFactory.create("POINTWISE_GCI", project),
            JobFactory.create("POINTWISE_MESH2", project),
            JobFactory.create("FLUENT2FENSAP", project),
        ]


