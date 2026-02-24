from __future__ import annotations

import sys
from pathlib import Path

import pyvista as pv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow

from .cameraservice import CameraService
from .filedialogservice import FileDialogService
from .infopresenter import InfoPresenter
from .messageboxservice import MessageBoxService
from .renderservice import RenderService
from .viewerstate import ViewerState
from .viewerui import ComboLoader, ScenePresenter, ViewerUiBuilder
from .zoneservice import ZoneService


class TecplotViewer(QMainWindow):
    """External integration points: open, clear, apply, save."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tecplot Viewer (PySide6 + PyVistaQt)")
        self.resize(1300, 850)

        self.state = ViewerState()
        self._loaded: pv.DataSet | pv.MultiBlock | None = None

        self.ui_builder = ViewerUiBuilder()
        self.combo_loader = ComboLoader()
        self.scene_presenter = ScenePresenter()

        self.ui_builder.build(self)
        self.ui_builder.bind(self)

        self.plotter.set_background("white")
        try:
            self.plotter.ren_win.SetMultiSamples(0)
        except Exception:
            pass
        self.plotter.show_axes()

        self.combo_loader.load_zone_options(self.zone_combo, [])
        self.combo_loader.load_scalar_options(self.scalar_combo, [])

    def open(self) -> None:
        path = FileDialogService.open_mesh_file(self)
        if not path:
            return

        try:
            obj = pv.read(path)
        except Exception as exc:
            MessageBoxService.show_load_error(self, path, exc)
            return

        self._loaded = obj
        self.state.path = Path(path)
        self.state.zones = ZoneService.extract_zones(obj)
        if not self.state.zones:
            MessageBoxService.show_load_error(self, path, "No renderable zones found.")
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

        self.plotter.camera_position = camera_tuple
        self.plotter.render()

    def clear(self) -> None:
        self.state = ViewerState()
        self._loaded = None

        self.plotter.clear()
        self.plotter.show_axes()
        self.plotter.reset_camera()
        self.plotter.render()

        self.combo_loader.load_zone_options(self.zone_combo, [])
        self.combo_loader.load_scalar_options(self.scalar_combo, [])
        self.info.setText("No file loaded.")

    def save(self) -> None:
        if not self.state.zones or not self.state.active_indices:
            MessageBoxService.show_no_screenshot_data(self)
            return

        path = FileDialogService.save_screenshot_file(self)
        if not path:
            return

        try:
            self.plotter.screenshot(path)
        except Exception as exc:
            MessageBoxService.show_screenshot_error(self, path, exc)


def main() -> int:
    pv.global_theme.window_size = [1300, 850]
    pv.global_theme.smooth_shading = True

    app = QApplication(sys.argv)
    viewer = TecplotViewer()
    viewer.show()
    return app.exec()
