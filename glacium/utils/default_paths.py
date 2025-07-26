from __future__ import annotations

from pathlib import Path

from .resource_locator import ResourceLocator


_locator = ResourceLocator()


def global_default_config() -> Path:
    """Return the path to ``config/defaults/global_default.yaml``."""

    return _locator.global_default_config()


def default_case_file() -> Path:
    """Return the path to ``config/defaults/case.yaml``."""

    return _locator.default_case_file()


def dejavu_font_file() -> Path:
    """Return the path to ``DejaVuSans.ttf`` used for PDF reports."""

    return _locator.dejavu_font_file()
