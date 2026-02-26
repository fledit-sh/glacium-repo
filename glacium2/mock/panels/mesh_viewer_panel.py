from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QLabel

from ..panel_api import Panel


class MeshViewerPanel(Panel):
    panel_id = "panel.mesh_viewer"
    title = "Mesh Viewer"
    default_dock_area = Qt.RightDockWidgetArea
    is_dock = False  # central tab

    def __init__(self, log_bus, parent=None) -> None:
        super().__init__(log_bus, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Embed your existing 3D viewer widget here."))
        layout.addStretch(1)

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from ..panel_api import LogBus
    app = QApplication(sys.argv)
    w = MeshViewerPanel(LogBus())
    w.resize(800, 400)
    w.show()
    raise SystemExit(app.exec())