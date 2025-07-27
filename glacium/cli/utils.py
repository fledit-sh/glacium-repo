"""Helpers for CLI commands."""

from __future__ import annotations

from pathlib import Path

import click


def runs_root() -> Path:
    """Return the project directory from the current Click context."""

    ctx = click.get_current_context(silent=True)
    root = getattr(ctx, "obj", None)
    return Path(root) if root is not None else Path("runs")

