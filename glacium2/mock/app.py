from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from .window import MainWindow
from .core.panelspec import PanelSpec
from .core.registry import Registry

from .panels.skeleton_panel import SkeletonPanel
from .panels.mesh_viewer_panel import MeshViewerPanel
from .panels.plots_panel import PlotsPanel


def create_registry() -> Registry:
    reg = Registry()
    reg.add(
        PanelSpec(
            id="panel.skeleton",
            title="Skeleton",
            dock=True,
            area=SkeletonPanel.default_dock_area,
            factory=lambda log: SkeletonPanel(log),
        )
    )
    reg.add(
        PanelSpec(
            id="panel.mesh_viewer",
            title="Mesh Viewer",
            dock=False,
            area=MeshViewerPanel.default_dock_area,
            factory=lambda log: MeshViewerPanel(log),
        )
    )
    reg.add(
        PanelSpec(
            id="panel.plots",
            title="Plots",
            dock=False,
            area=PlotsPanel.default_dock_area,
            factory=lambda log: PlotsPanel(log),
        )
    )
    return reg


def run() -> int:
    app = QApplication(sys.argv)
    reg = create_registry()
    win = MainWindow(reg)
    win.resize(1300, 800)
    win.show()
    return app.exec()