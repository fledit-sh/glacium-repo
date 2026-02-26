from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

from ..panel_api import Panel


class SkeletonPanel(Panel):
    panel_id = "panel.skeleton"
    title = "Project Skeleton"
    default_dock_area = Qt.LeftDockWidgetArea
    is_dock = True

    def __init__(self, log_bus, parent=None) -> None:
        super().__init__(log_bus, parent)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Skeleton manager POC"))
        btn = QPushButton("Init skeleton (demo)")
        btn.clicked.connect(self._on_init)
        layout.addWidget(btn)
        layout.addStretch(1)

    def _on_init(self) -> None:
        self.log("Init skeleton clicked (wire your H5 code here).")

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from ..panel_api import LogBus
    app = QApplication(sys.argv)
    w = SkeletonPanel(LogBus())
    w.resize(800, 400)
    w.show()
    raise SystemExit(app.exec())