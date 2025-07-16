"""Registry and factory for available recipes.

Recipes are small classes that build a list of jobs for a project.  They are
registered automatically on import and can be instantiated by name.

Example
-------
>>> RecipeManager.list()
['default_aero']
>>> recipe = RecipeManager.create('default_aero')
"""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Type

from glacium.utils.logging import log

# Basisklasse --------------------------------------------------------------
class BaseRecipe:
    """Base class for all recipes."""

    name: str = "base"
    description: str = "(no description)"

    def build(self, project):  # noqa: D401
        """Return a list of job instances for ``project``."""

        raise NotImplementedError


# Registry -----------------------------------------------------------------
class RecipeManager:
    _recipes: Dict[str, Type[BaseRecipe]] | None = None

    # Factory --------------------------------------------------------------
    @classmethod
    def create(cls, name: str) -> BaseRecipe:
        """Instantiate the recipe with the given ``name``.

        Parameters
        ----------
        name:
            Registered name of the recipe.
        Example
        -------
        >>> RecipeManager.create('default_aero')
        """

        cls._load()

        if "+" in name:
            from glacium.recipes.composite import CompositeRecipe

            parts = [n for n in name.split("+") if n]
            return CompositeRecipe(parts)

        if name not in cls._recipes:  # type: ignore
            raise KeyError(f"Recipe '{name}' nicht registriert.")
        return cls._recipes[name]()  # type: ignore[index]

    @classmethod
    def list(cls) -> List[str]:
        """Return all registered recipe names.

        Example
        -------
        >>> RecipeManager.list()
        ['default_aero']
        """

        cls._load()
        return sorted(cls._recipes)  # type: ignore[arg-type]

    # Decorator ------------------------------------------------------------
    @classmethod
    def register(cls, recipe_cls: Type[BaseRecipe]):
        """Class decorator to register a ``recipe_cls``.

        Parameters
        ----------
        recipe_cls:
            Class deriving from :class:`BaseRecipe`.
        """

        cls._load()
        if recipe_cls.name in cls._recipes:  # type: ignore
            log.warning(f"Recipe '{recipe_cls.name}' wird überschrieben.")
        cls._recipes[recipe_cls.name] = recipe_cls  # type: ignore[index]
        return recipe_cls

    # Internal loader ------------------------------------------------------
    @classmethod
    def _load(cls):
        """Populate the internal recipe registry if empty."""

        if cls._recipes is not None:
            return
        cls._recipes = {}
        cls._discover("glacium.recipes")
        log.debug(f"Recipes: {', '.join(cls._recipes)}")  # type: ignore[arg-type]

    @classmethod
    def _discover(cls, pkg_name: str):
        """Import all submodules from ``pkg_name`` to populate registry."""

        try:
            pkg = importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            return
        pkg_path = Path(pkg.__file__).parent
        for mod in pkgutil.iter_modules([str(pkg_path)]):
            importlib.import_module(f"{pkg_name}.{mod.name}")

