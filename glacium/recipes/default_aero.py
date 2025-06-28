from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
from glacium.engines.XfoilJobs import (
    XfoilRefineJob, XfoilThickenTEJob, XfoilBoundaryLayerJob,
    XfoilPolarsJob, XfoilSuctionCurveJob,
)

@RecipeManager.register
class DefaultAero(BaseRecipe):
    name = "default_aero"
    description = "Kompletter XFOIL-Workflow"

    def build(self, project):
        return [
            XfoilRefineJob(project),
            XfoilThickenTEJob(project),
            XfoilBoundaryLayerJob(project),
            XfoilPolarsJob(project),
            XfoilSuctionCurveJob(project),
        ]

@RecipeManager.register
class DefaultAero(BaseRecipe):
    name = "minimal_xfoil"
    description = "Minimaler XFOIL-Workflow"

    def build(self, project):
        return [
            XfoilRefineJob(project),
            XfoilThickenTEJob(project),
        ]