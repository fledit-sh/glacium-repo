from __future__ import annotations

"""Utilities for working with Jinja templates."""

from jinja2 import Environment

from .templates import filters as _filters

__all__ = ["register_filters"]


def register_filters(env: Environment) -> None:
    """Register custom filters on ``env``."""
    for name in _filters.__all__:
        env.filters[name] = getattr(_filters, name)
