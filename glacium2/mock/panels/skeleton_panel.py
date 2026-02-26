from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout

from ..core.panel import Panel
from ..services import Logger, ProjectStore, Settings


class SkeletonPanel(Panel):
    panel_id = "panel.skeleton"
    title = "Project Skeleton"
    default_dock_area = Qt.LeftDockWidgetArea
    is_dock = True

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
        layout.addWidget(QLabel("Skeleton manager POC"))
        btn = QPushButton("Init skeleton (demo)")
        btn.clicked.connect(self.init)
        layout.addWidget(btn)
        layout.addStretch(1)

    def init(self) -> None:
        self.log("Init skeleton clicked (wire your H5 code here).")


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    from ..core.logbus import LogBus

    app = QApplication(sys.argv)
    w = SkeletonPanel(LogBus(), Logger(), Settings(), ProjectStore())
    w.resize(800, 400)
    w.show()
    raise SystemExit(app.exec())
