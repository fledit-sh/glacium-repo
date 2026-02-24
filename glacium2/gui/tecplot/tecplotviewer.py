from __future__ import annotations

import sys
from pathlib import Path

import pyvista as pv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow

from .cameraservice import CameraService
from .dialogport import DialogPort
from .infopresenter import InfoPresenter
from .meshreader import MeshReader
from .messageport import MessagePort
from .plotterport import PlotterPort
from .pyvistaplotter import PyVistaPlotter
from .pyvistareader import PyVistaReader
from .qtfiledialog import QtFileDialog
from .qtmessagebox import QtMessageBox
from .renderservice import RenderService
from .viewerstate import ViewerState
from .viewerui import ComboLoader, ScenePresenter, ViewerUiBuilder
from .zoneservice import ZoneService


class TecplotViewer(QMainWindow):
    """External integration points: open, clear, apply, save."""

    def __init__(
        self,
        mesh_reader: MeshReader | None = None,
        plotter: PlotterPort | None = None,
        dialog: DialogPort | None = None,
        message: MessagePort | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Tecplot Viewer (PySide6 + PyVistaQt)")
        self.resize(1300, 850)

        self.state = ViewerState()
        self._loaded: pv.DataSet | pv.MultiBlock | None = None

        self.ui_builder = ViewerUiBuilder()
        self.combo_loader = ComboLoader()
        self.scene_presenter = ScenePresenter()

        self.mesh_reader = mesh_reader or PyVistaReader()
        self.plotter = plotter or PyVistaPlotter(self)
        self.dialog = dialog or QtFileDialog(self)
        self.message = message or QtMessageBox(self)

        self.ui_builder.build(self, self.plotter)
        self.ui_builder.bind(self)

        if isinstance(self.plotter, PyVistaPlotter):
            self.plotter.setup()
        else:
            self.plotter.axes()

        self.combo_loader.load_zone_options(self.zone_combo, [])
        self.combo_loader.load_scalar_options(self.scalar_combo, [])

    def open(self) -> None:
        path = self.dialog.open()
        if not path:
            return

        try:
            obj = self.mesh_reader.read(path)
        except Exception as exc:
            self.message.error("Load error", f"Could not open file.\n{path}\n\n{exc}")
            return

        self._loaded = obj
        self.state.path = Path(path)
        self.state.zones = ZoneService.extract_zones(obj)
        if not self.state.zones:
            self.message.error("Load error", f"Could not open file.\n{path}\n\nNo renderable zones found.")
            return

        self.combo_loader.load_zone_options(self.zone_combo, self.state.zones)
        self.zone_combo.setCurrentIndex(0)

    def select(self, idx: int) -> None:
        if not self.state.zones:
            return

        current_scalar_text = self.scalar_combo.currentText()
        self.state.active_indices = ZoneService.select_active_indices(self.state.zones, idx)
        scalar_names = ZoneService.scalar_names_for_active(self.state)
        self.state.active_scalar = ZoneService.derive(scalar_names, current_scalar_text)

        self.combo_loader.load_scalar_options(self.scalar_combo, scalar_names)
        scalar_idx = self.scalar_combo.findText(self.state.active_scalar, Qt.MatchExactly)
        self.scalar_combo.setCurrentIndex(scalar_idx if scalar_idx >= 0 else 0)

        self.render_scene()

        self.view_combo.setCurrentText("Isometric")
        self.apply()

    def scalar(self, idx: int) -> None:
        if not self.state.zones or not self.state.active_indices:
            return

        current_text = self.scalar_combo.itemText(idx) if idx >= 0 else self.scalar_combo.currentText()
        scalar_names = ZoneService.scalar_names_for_active(self.state)
        self.state.active_scalar = ZoneService.derive(scalar_names, current_text)

        scalar_idx = self.scalar_combo.findText(self.state.active_scalar, Qt.MatchExactly)
        self.scalar_combo.blockSignals(True)
        self.scalar_combo.setCurrentIndex(scalar_idx if scalar_idx >= 0 else 0)
        self.scalar_combo.blockSignals(False)

        self.render_scene()

    def render_scene(self) -> None:
        self.scene_presenter.render(self.plotter, self.state, self.info, RenderService, InfoPresenter)

    def apply(self) -> None:
        if not self.state.zones or not self.state.active_indices:
            return

        datasets = [self.state.zones[i].dataset for i in self.state.active_indices]
        bounds = CameraService.bounds_union(datasets)
        center = CameraService.scene_center(bounds)
        radius = CameraService.camera_radius(bounds)
        camera_tuple = CameraService.camera_from_preset(center, radius, self.view_combo.currentText())
        if camera_tuple is None:
            return

        self.plotter.camera(camera_tuple)
        self.plotter.render()

    def clear(self) -> None:
        self.state = ViewerState()
        self._loaded = None

        self.plotter.clear()
        self.plotter.axes()
        self.plotter.render()

        self.combo_loader.load_zone_options(self.zone_combo, [])
        self.combo_loader.load_scalar_options(self.scalar_combo, [])
        self.info.setText("No file loaded.")

    def save(self) -> None:
        if not self.state.zones or not self.state.active_indices:
            self.message.info("Screenshot", "Nothing to screenshot.")
            return

        path = self.dialog.save()
        if not path:
            return

        try:
            self.plotter.shot(path)
        except Exception as exc:
            self.message.error("Screenshot error", f"Could not save screenshot.\n{path}\n\n{exc}")


def main() -> int:
    pv.global_theme.window_size = [1300, 850]
    pv.global_theme.smooth_shading = True

    app = QApplication(sys.argv)
    viewer = TecplotViewer()
    viewer.show()
    return app.exec()
