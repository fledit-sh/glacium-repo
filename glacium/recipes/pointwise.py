"""Recipe integrating Pointwise mesh generation jobs."""

from glacium.managers.recipe_manager import RecipeManager, BaseRecipe
from glacium.utils.job_index import JobFactory
from glacium.engines.pointwise import PointwiseEngine

@RecipeManager.register
class PointwiseRecipe(BaseRecipe):
    """Run the Pointwise GCI and mesh generation scripts."""

    name = "pointwise"
    description = "Run Pointwise mesh scripts"

    def build(self, project):
        return [
            JobFactory.create("POINTWISE_GCI", project, engine=PointwiseEngine),
            JobFactory.create("POINTWISE_MESH2", project, engine=PointwiseEngine),
            JobFactory.create("FLUENT2FENSAP", project),
        ]


