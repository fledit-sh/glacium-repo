from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
from glacium.engines.PointwiseJobs import PointwiseGCIJob, PointwiseMesh2Job

@RecipeManager.register
class PointwiseRecipe(BaseRecipe):
    name = "pointwise"
    description = "Run Pointwise mesh scripts"

    def build(self, project):
        return [
            PointwiseGCIJob(project),
            PointwiseMesh2Job(project),
        ]

