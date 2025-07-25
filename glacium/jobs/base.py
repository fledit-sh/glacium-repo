from __future__ import annotations

"""Compatibility aliases for job base classes."""

from glacium.core.base import ScriptJobBase, PythonJobBase


ScriptJob = ScriptJobBase
PythonJob = PythonJobBase

__all__ = ["ScriptJob", "PythonJob", "ScriptJobBase", "PythonJobBase"]
