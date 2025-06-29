"""Recipe containing jobs to run the FENSAP solver."""

from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
from glacium.engines.fensap import FensapRunJob

@RecipeManager.register
class FensapRecipe(BaseRecipe):
    """Run the FENSAP solver."""

    name = "fensap"
    description = "Run fensap scripts"
    def build(self, project):
        return [
            FensapRunJob(project),
        ]


