import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import importlib
from importlib import metadata
import pytest


def test_import_without_distribution(monkeypatch):
    """``import glacium`` should succeed without installed metadata."""
    def raise_pkg_not_found(name):
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(metadata, "version", raise_pkg_not_found)

    sys.modules.pop("glacium", None)
    module = importlib.import_module("glacium")

    assert module.__version__ == "0.0.0"
