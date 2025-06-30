"""Jobs grouped into preprocessing and solver workflows."""

from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
from glacium.engines.XfoilJobs import XfoilRefineJob, XfoilThickenTEJob
from glacium.engines.XfoilConvertJob import XfoilConvertJob
from glacium.engines.PointwiseJobs import PointwiseGCIJob
from glacium.engines.fluent2fensap import Fluent2FensapJob
from glacium.engines.fensap import FensapRunJob, Drop3dRunJob, Ice3dRunJob


@RecipeManager.register
class PreprocessingRecipe(BaseRecipe):
    """Basic preprocessing chain from XFOIL to fluent2fensap."""

    name = "preprocessing"
    description = "XFOIL to Fluent2Fensap preprocessing workflow"

    def build(self, project):
        jobs = [
            XfoilRefineJob(project),
            XfoilThickenTEJob(project),
            XfoilConvertJob(project),
            PointwiseGCIJob(project),
            Fluent2FensapJob(project),
        ]
        # chain dependencies in order of jobs list
        for prev, cur in zip(jobs, jobs[1:]):
            cur.deps = (prev.name,)
        return jobs


@RecipeManager.register
class SolverRecipe(BaseRecipe):
    """Run FENSAP and post-processors in sequence."""

    name = "solver"
    description = "Fensap, Drop3d and Ice3d solver workflow"

    def build(self, project):
        jobs = [
            FensapRunJob(project),
            Drop3dRunJob(project),
            Ice3dRunJob(project),
        ]
        for prev, cur in zip(jobs, jobs[1:]):
            cur.deps = (prev.name,)
        return jobs
