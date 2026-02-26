from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .core.panelspec import PanelSpec
from .core.registry import Registry
from .panels.mesh_viewer_panel import MeshViewerPanel
from .panels.plots_panel import PlotsPanel
from .panels.skeleton_panel import SkeletonPanel
from .services import Logger, ProjectStore, Settings
from .window import MainWindow


PANEL_SPECS: tuple[PanelSpec, ...] = (
    PanelSpec(
        id="panel.skeleton",
        title="Project Skeleton",
        area=SkeletonPanel.default_dock_area,
        factory=lambda log, logger, settings, project_store: SkeletonPanel(
            log, logger, settings, project_store
        ),
    ),
    PanelSpec(
        id="panel.plots",
        title="Plots",
        area=PlotsPanel.default_dock_area,
        factory=lambda log, logger, settings, project_store: PlotsPanel(
            log, logger, settings, project_store
        ),
    ),
    PanelSpec(
        id="panel.mesh_viewer",
        title="Mesh Viewer",
        area=MeshViewerPanel.default_dock_area,
        factory=lambda log, logger, settings, project_store: MeshViewerPanel(
            log, logger, settings, project_store
        ),
        dock=False,
        workspace=True,
    ),
)


def create_registry() -> Registry:
    reg = Registry()
    for spec in PANEL_SPECS:
        reg.add(spec)
    return reg


def run() -> int:
    app = QApplication(sys.argv)
    reg = create_registry()
    logger = Logger()
    settings = Settings()
    project_store = ProjectStore()
    win = MainWindow(reg, logger, settings, project_store)
    win.resize(1300, 800)
    win.show()
    return app.exec()
