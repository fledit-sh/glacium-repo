"""Recipe executing the FENSAP solver chain."""

from glacium.managers.recipe_manager import RecipeManager, BaseRecipe
from glacium.utils.JobIndex import JobFactory


@RecipeManager.register
class SolverRecipe(BaseRecipe):
    """Run FENSAP and related solvers."""

    name = "solver"
    description = "Run FENSAP, DROP3D and ICE3D"

    def build(self, project):
        return [
            JobFactory.create("FENSAP_RUN", project),
            JobFactory.create("FENSAP_CONVERGENCE_STATS", project),
            JobFactory.create("DROP3D_RUN", project),
            JobFactory.create("DROP3D_CONVERGENCE_STATS", project),
            JobFactory.create("ICE3D_RUN", project),
            JobFactory.create("ICE3D_CONVERGENCE_STATS", project),
        ]
