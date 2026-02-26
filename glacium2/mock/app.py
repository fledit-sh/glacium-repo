from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from .window import MainWindow
from .core.panelspec import PanelSpec
from .core.registry import Registry

from .panels.skeleton_panel import SkeletonPanel
from .panels.mesh_viewer_panel import MeshViewerPanel
from .panels.plots_panel import PlotsPanel


PANEL_SPECS: tuple[PanelSpec, ...] = (
    PanelSpec(
        id="panel.skeleton",
        title="Project Skeleton",
        area=SkeletonPanel.default_dock_area,
        factory=lambda log: SkeletonPanel(log),
    ),
    PanelSpec(
        id="panel.plots",
        title="Plots",
        area=PlotsPanel.default_dock_area,
        factory=lambda log: PlotsPanel(log),
    ),
    PanelSpec(
        id="panel.mesh_viewer",
        title="Mesh Viewer",
        area=MeshViewerPanel.default_dock_area,
        factory=lambda log: MeshViewerPanel(log),
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
    win = MainWindow(reg)
    win.resize(1300, 800)
    win.show()
    return app.exec()
