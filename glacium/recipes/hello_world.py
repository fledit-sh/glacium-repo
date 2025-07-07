"""Minimal example recipe used for tests."""

from glacium.managers.recipe_manager import BaseRecipe, RecipeManager
from glacium.models.job import Job
from glacium.utils.JobIndex import JobFactory
from glacium.utils.logging import log_call


class HelloJob(Job):
    """Simple job that prints a greeting."""

    name = "HelloJob"
    deps = ()

    @log_call
    def execute(self):
        from glacium.utils.logging import log

        log.info("Hello from a dummy job")


@RecipeManager.register
class HelloWorldRecipe(BaseRecipe):
    """Recipe that contains a single :class:`HelloJob`."""

    name = "hello"
    description = "single dummy job"

    def build(self, project):
        return [JobFactory.create("HelloJob", project)]
