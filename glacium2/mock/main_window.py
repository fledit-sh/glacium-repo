from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QTabWidget, QTextEdit, QWidget, QToolBar, QFileDialog
)

from .panel_api import LogBus, PanelRegistry


class MainWindow(QMainWindow):
    def __init__(self, registry: PanelRegistry) -> None:
        super().__init__()
        self.setWindowTitle("Glacium")

        self._log_bus = LogBus()
        self._registry = registry

        self._central_tabs = QTabWidget()
        self.setCentralWidget(self._central_tabs)

        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        log_dock = QDockWidget("Log", self)
        log_dock.setWidget(self._log_view)
        self.addDockWidget(Qt.BottomDockWidgetArea, log_dock)

        self._log_bus.message.connect(self._append_log)

        self._build_toolbar()
        self._build_panels()

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main", self)
        self.addToolBar(tb)

        open_action = tb.addAction("Open Project…")
        open_action.triggered.connect(self._open_project_dialog)

    def _build_panels(self) -> None:
        for spec in self._registry.specs().values():
            panel = spec.factory(self._log_bus)

            if spec.is_dock:
                dock = QDockWidget(spec.title, self)
                dock.setObjectName(spec.panel_id)  # useful for saving state later
                dock.setWidget(panel)
                self.addDockWidget(spec.default_dock_area, dock)
            else:
                self._central_tabs.addTab(panel, spec.title)

    def _append_log(self, msg: str) -> None:
        self._log_view.append(msg)

    def _open_project_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open H5 project", "", "HDF5 (*.h5 *.hdf5)")
        if not path:
            return
        self._log_bus.message.emit(f"[app] Opened project: {path}")

        # notify panels
        for i in range(self._central_tabs.count()):
            w = self._central_tabs.widget(i)
            if hasattr(w, "on_project_opened"):
                w.on_project_opened(path)

        # dock widgets: iterate children
        for dock in self.findChildren(QDockWidget):
            w = dock.widget()
            if hasattr(w, "on_project_opened"):
                w.on_project_opened(path)