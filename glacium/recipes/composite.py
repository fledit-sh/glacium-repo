"""Recipe concatenating multiple recipes."""

from __future__ import annotations

from glacium.managers.recipe_manager import RecipeManager, BaseRecipe


class CompositeRecipe(BaseRecipe):
    """Combine several recipes into one."""

    name = "composite"
    description = "Concatenate recipes"

    def __init__(self, recipe_names: list[str]):
        self.recipe_names = recipe_names
        self._recipes = [RecipeManager.create(n) for n in recipe_names]

    def build(self, project):
        jobs = []
        for recipe in self._recipes:
            jobs.extend(recipe.build(project))
        return jobs
