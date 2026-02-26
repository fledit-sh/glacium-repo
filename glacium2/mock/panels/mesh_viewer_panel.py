from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

from ..core.panel import Panel
from ..services import Logger, ProjectStore, Settings


class MeshViewerPanel(Panel):
    panel_id = "panel.mesh_viewer"
    title = "Mesh Viewer"
    default_dock_area = Qt.RightDockWidgetArea
    is_dock = False  # central tab

    def __init__(
        self,
        log_bus,
        logger: Logger,
        settings: Settings,
        project_store: ProjectStore,
        parent=None,
    ) -> None:
        super().__init__(log_bus, logger, settings, project_store, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Embed your existing 3D viewer widget here."))
        layout.addStretch(1)


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    from ..core.logbus import LogBus

    app = QApplication(sys.argv)
    w = MeshViewerPanel(LogBus(), Logger(), Settings(), ProjectStore())
    w.resize(800, 400)
    w.show()
    raise SystemExit(app.exec())
