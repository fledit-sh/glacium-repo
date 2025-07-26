"""Recipe running grid dependencies and FENSAP."""

from glacium.managers.recipe_manager import RecipeManager, BaseRecipe
from glacium.utils.job_index import JobFactory
from glacium.engines.pointwise import PointwiseEngine
from glacium.engines.fensap import FensapEngine


@RecipeManager.register
class GridDependencyRecipe(BaseRecipe):
    """Refine profile, generate mesh and run FENSAP."""

    name = "grid_dep"
    description = "XFOIL refinement, mesh generation and FENSAP run"

    def build(self, project):
        return [
            JobFactory.create("XFOIL_REFINE", project),
            JobFactory.create("XFOIL_THICKEN_TE", project),
            JobFactory.create("XFOIL_PW_CONVERT", project),
            JobFactory.create("POINTWISE_GCI", project, engine=PointwiseEngine),
            JobFactory.create("FLUENT2FENSAP", project),
            JobFactory.create("FENSAP_RUN", project, engine=FensapEngine),
            JobFactory.create("FENSAP_CONVERGENCE_STATS", project),
        ]
