"""Recipe running FENSAP solver and post-processing jobs."""

from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
from glacium.engines.fensap import FensapRunJob, Drop3dRunJob, Ice3dRunJob


@RecipeManager.register
class FensapRecipe(BaseRecipe):
    """Sequence of FENSAP solver jobs."""

    name = "fensap"
    description = "Run FENSAP solver workflow"

    def build(self, project):
        return [
            FensapRunJob(project),
            Drop3dRunJob(project),
            Ice3dRunJob(project),
        ]

