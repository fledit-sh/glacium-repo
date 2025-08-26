"""Tests for the ``scripts/12_polar_compare.py`` helpers."""

from __future__ import annotations

import runpy
from pathlib import Path


def load_module() -> dict[str, object]:
    """Return the module globals for ``12_polar_compare.py``."""
    script = Path(__file__).resolve().parents[1] / "scripts" / "12_polar_compare.py"
    return runpy.run_path(script)


def test_first_drop_index_includes_drop_point() -> None:
    module = load_module()
    first_drop_index = module["first_drop_index"]

    vals = [0.1, 0.5, 0.8, 0.6, 0.55]
    cut = first_drop_index(vals)
    assert cut == 4
    assert vals[:cut][-1] == 0.6


def test_first_drop_index_no_drop() -> None:
    module = load_module()
    first_drop_index = module["first_drop_index"]

    vals = [0.1, 0.2, 0.3]
    cut = first_drop_index(vals)
    assert cut == len(vals)
