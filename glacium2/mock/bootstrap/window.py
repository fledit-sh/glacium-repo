from __future__ import annotations

from ..core.registry import Registry
from ..window import MainWindow
from .services import Services


def build(registry: Registry, services: Services) -> MainWindow:
    return MainWindow(
        registry,
        services.logger,
        services.settings,
        services.project_store,
    )
