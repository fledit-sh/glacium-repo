"""Recipe executing the FENSAP solver chain."""

from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
from glacium.engines.fensap import FensapRunJob, Drop3dRunJob, Ice3dRunJob


@RecipeManager.register
class SolverRecipe(BaseRecipe):
    """Run FENSAP and related solvers."""

    name = "solver"
    description = "Run FENSAP, DROP3D and ICE3D"

    def build(self, project):
        return [
            FensapRunJob(project),
            Drop3dRunJob(project),
            Ice3dRunJob(project),
        ]
