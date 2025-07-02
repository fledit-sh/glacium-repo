"""Recipe running FENSAP solver and post-processing jobs."""

from glacium.engines.fensap import (
    Drop3dRunJob,
    FensapRunJob,
    Ice3dRunJob,
    MultiShotRunJob,
)
from glacium.managers.RecipeManager import BaseRecipe, RecipeManager


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
            MultiShotRunJob,
        ]
