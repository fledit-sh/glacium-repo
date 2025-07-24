"""Engine implementations wrapping external solver calls."""
from __future__ import annotations

from importlib import import_module

__all__ = [
    "BaseEngine",
    "XfoilEngine",
    "DummyEngine",
    "PointwiseEngine",
    "PointwiseScriptJob",
    "FensapEngine",
    "FensapScriptJob",
    "EngineFactory",
]

_module_map = {
    "BaseEngine": "glacium.engines.base_engine",
    "XfoilEngine": "glacium.engines.base_engine",
    "DummyEngine": "glacium.engines.base_engine",
    "PointwiseEngine": "glacium.engines.pointwise",
    "PointwiseScriptJob": "glacium.engines.pointwise",
    "FensapEngine": "glacium.engines.fensap",
    "FensapScriptJob": "glacium.engines.fensap",
    "EngineFactory": "glacium.engines.engine_factory",
}


def __getattr__(name: str):
    if name in _module_map:
        module = import_module(_module_map[name])
        return getattr(module, name)
    raise AttributeError(name)
