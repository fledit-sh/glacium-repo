"""Recipe integrating Pointwise mesh generation jobs."""

from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
from glacium.engines.fensap import FensapEngine

@RecipeManager.register
class FensapRecipe(BaseRecipe):
    """Run the Pointwise GCI and mesh generation scripts."""

    name = "fensap"
    description = "Run fensap scripts"

    def build(self, project):
        return [
            FensapEngine(project),
        ]