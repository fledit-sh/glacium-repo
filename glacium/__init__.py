# !/usr/bin/env python
"""Title.

Description
"""
# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

from __future__ import annotations

# -----------------------------------------------------------------------------
# COPYRIGHT
# -----------------------------------------------------------------------------

__author__ = "Noel Ernsting Luz"
__copyright__ = "Copyright (C) 2022 Noel Ernsting Luz"
__license__ = "Public Domain"
from importlib.metadata import PackageNotFoundError, version as _version

# Use a fallback version if package metadata is missing.  This allows
# ``import glacium`` to succeed when the project has not been installed
# as a distribution.
try:  # pragma: no cover - executed in tests via monkeypatch
    __version__ = _version("glacium")
except PackageNotFoundError:  # package is not installed
    __version__ = "0.0.0"


# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# LOGGER
# -----------------------------------------------------------------------------

# The main logger is configured in :mod:`glacium.utils.logging`.

# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

from .api import Run

__all__ = ["Run"]
