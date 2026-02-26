from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout

from ..core.panel import Panel
from ..services import Logger, ProjectStore, Settings


class PlotsPanel(Panel):
    panel_id = "panel.plots"
    title = "Plots"
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
        layout.addWidget(QLabel("Papergrade plot generator (hook your scripts)."))
        btn = QPushButton("Generate demo plot")
        btn.clicked.connect(lambda: self.log("Plot generation triggered."))
        layout.addWidget(btn)
        layout.addStretch(1)


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    from ..core.logbus import LogBus

    app = QApplication(sys.argv)
    w = PlotsPanel(LogBus(), Logger(), Settings(), ProjectStore())
    w.resize(800, 400)
    w.show()
    raise SystemExit(app.exec())
