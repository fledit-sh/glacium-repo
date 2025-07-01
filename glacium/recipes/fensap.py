"""Recipe integrating Pointwise mesh generation jobs."""

from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
from glacium.engines.fensap import FensapEngine
from glacium.utils.logging import log

@RecipeManager.register
class FensapRecipe(BaseRecipe):
    """Run the Pointwise GCI and mesh generation scripts."""

    name = "fensap"
    description = "Run fensap scripts"
    def build(self, project):
        return [
            FensapEngine(project),
        ]


# -----------------------------------------------------------------------------
# COPYRIGHT
# -----------------------------------------------------------------------------

__author__ = "Noel Ernsting Luz"
__copyright__ = "Copyright (C) 2022 Noel Ernsting Luz"
__license__ = "Public Domain"
from importlib.metadata import version as _version
__version__ = _version("glacium")

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# LOGGER
# -----------------------------------------------------------------------------

# ``log`` is shared across all modules

# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

