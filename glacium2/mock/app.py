from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow
from .core.registry import Registry

from .panels.skeleton_panel import SkeletonPanel
from .panels.mesh_viewer_panel import MeshViewerPanel
from .panels.plots_panel import PlotsPanel


def create_registry() -> Registry:
    reg = Registry()
    reg.add(lambda log: SkeletonPanel(log))
    reg.add(lambda log: MeshViewerPanel(log))
    reg.add(lambda log: PlotsPanel(log))
    return reg


def run() -> int:
    app = QApplication(sys.argv)
    reg = create_registry()
    win = MainWindow(reg)
    win.resize(1300, 800)
    win.show()
    return app.exec()