"""Recipe containing jobs to run the FENSAP solver."""

from glacium.managers.recipe_manager import RecipeManager, BaseRecipe
from glacium.jobs.fensap_jobs import FensapRunJob

@RecipeManager.register
class FensapRecipe(BaseRecipe):
    """Run the FENSAP solver."""

    name = "fensap"
    description = "Run fensap scripts"
    def build(self, project):
        return [
            FensapRunJob(project),
        ]


