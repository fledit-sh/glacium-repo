from __future__ import annotations

"""Utilities for selecting multishot projects.

This module exposes :func:`load_multishot_project` which locates the multishot
project under a given directory that contains the most shot entries.  It avoids
looking for solver output files and instead bases the selection purely on the
``CASE_MULTISHOT`` values stored in each project's configuration.
"""

from glacium.utils.multishot import load_multishot_project

__all__ = ["load_multishot_project"]
