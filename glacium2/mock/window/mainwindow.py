from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QTextEdit

from ..core.logbus import LogBus
from ..core.registry import Registry
from .docks import DockBuilder
from .router import OpenProjectRouter
from .shell import WindowShell
from .toolbar import ToolbarBuilder


class MainWindow(WindowShell):
    def __init__(self, registry: Registry) -> None:
        super().__init__("Glacium")
        self._log_bus = LogBus()
        self._registry = registry
        self._router = OpenProjectRouter()
        self._docks = DockBuilder(self)
        self._toolbar = ToolbarBuilder(self)
        self._log_view = QTextEdit()

        self.build()

    def build(self) -> None:
        super().build()

        self._log_view.setReadOnly(True)
        self._docks.add("Log", self._log_view, Qt.BottomDockWidgetArea, name="log")

        self._log_bus.message.connect(self._log_view.append)
        self._toolbar.build(self.open)

        for spec in self._registry.items().values():
            panel = spec.factory(self._log_bus)
            self._router.bind(panel)

            if spec.is_dock:
                self._docks.add(spec.title, panel, spec.default_dock_area, name=spec.panel_id)
            else:
                self.add(panel, spec.title)

    def open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open project", "", "Project files (*)")
        if not path:
            return

        self._log_bus.message.emit(f"[app] Opened project: {path}")
        self._router.emit(path)
