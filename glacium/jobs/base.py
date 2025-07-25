from __future__ import annotations

from abc import ABC

from glacium.core.base import JobBase, ScriptJobBase, PythonJobBase


class ScriptJob(ScriptJobBase, ABC):
    """Compatibility wrapper for :class:`~glacium.core.base.ScriptJobBase`."""


class PythonJob(PythonJobBase, ABC):
    """Compatibility wrapper for :class:`~glacium.core.base.PythonJobBase`."""
