"""Recipe preparing meshes and conversions before solver runs."""

from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
from glacium.jobs.xfoil_jobs import XfoilRefineJob, XfoilThickenTEJob
from glacium.engines.xfoil_convert_job import XfoilConvertJob
from glacium.jobs.pointwise_jobs import PointwiseGCIJob
from glacium.engines.fluent2fensap import Fluent2FensapJob


@RecipeManager.register
class PrepRecipe(BaseRecipe):
    """Run the standard preparation workflow."""

    name = "prep"
    description = "Refine profile and generate initial mesh"

    def build(self, project):
        return [
            XfoilRefineJob(project),
            XfoilThickenTEJob(project),
            XfoilConvertJob(project),
            PointwiseGCIJob(project),
            Fluent2FensapJob(project),
        ]
