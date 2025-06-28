from glacium.managers.RecipeManager import BaseRecipe, RecipeManager
from glacium.models.job import Job

class HelloJob(Job):
    name = "HelloJob"
    deps = ()

    def execute(self):
        from glacium.utils.logging import log
        log.info("👋  Hello from a dummy job!")

@RecipeManager.register
class HelloWorldRecipe(BaseRecipe):
    name = "hello"
    description = "single dummy job"

    def build(self, project):
        return [HelloJob(project)]
