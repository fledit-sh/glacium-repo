"""glacium.managers.recipe_manager – Revised

* Registry / Service‑Locator
* Factory returns **instance** of recipe
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
    name: str = "base"
    description: str = "(no description)"

    def build(self, project):  # noqa: D401
        raise NotImplementedError


# Registry -----------------------------------------------------------------
class RecipeManager:
    _recipes: Dict[str, Type[BaseRecipe]] | None = None

    # Factory --------------------------------------------------------------
    @classmethod
    def create(cls, name: str) -> BaseRecipe:
        cls._load()
        if name not in cls._recipes:  # type: ignore
            raise KeyError(f"Recipe '{name}' nicht registriert.")
        return cls._recipes[name]()  # type: ignore[index]

    @classmethod
    def list(cls) -> List[str]:
        cls._load()
        return sorted(cls._recipes)  # type: ignore[arg-type]

    # Decorator ------------------------------------------------------------
    @classmethod
    def register(cls, recipe_cls: Type[BaseRecipe]):
        cls._load()
        if recipe_cls.name in cls._recipes:  # type: ignore
            log.warning(f"Recipe '{recipe_cls.name}' wird überschrieben.")
        cls._recipes[recipe_cls.name] = recipe_cls  # type: ignore[index]
        return recipe_cls

    # Internal loader ------------------------------------------------------
    @classmethod
    def _load(cls):
        if cls._recipes is not None:
            return
        cls._recipes = {}
        cls._discover("glacium.recipes")
        log.debug(f"Recipes: {', '.join(cls._recipes)}")  # type: ignore[arg-type]

    @classmethod
    def _discover(cls, pkg_name: str):
        try:
            pkg = importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            return
        pkg_path = Path(pkg.__file__).parent
        for mod in pkgutil.iter_modules([str(pkg_path)]):
            importlib.import_module(f"{pkg_name}.{mod.name}")
