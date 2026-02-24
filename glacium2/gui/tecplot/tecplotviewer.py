from __future__ import annotations

import sys
from pathlib import Path

import pyvista as pv
from pyvistaqt import QtInteractor

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .cameraservice import CameraService
from .filedialogservice import FileDialogService
from .infopresenter import InfoPresenter
from .messageboxservice import MessageBoxService
from .renderservice import RenderService
from .viewerstate import ViewerState, ZoneItem
from .zoneservice import ZoneService


class TecplotViewer(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tecplot Viewer (PySide6 + PyVistaQt)")
        self.resize(1300, 850)

        self.state = ViewerState()
        self._loaded: pv.DataSet | pv.MultiBlock | None = None

        self._build_widgets()
        self._build_main_layout()
        self._connect_signals()

        self.plotter.set_background("white")
        try:
            self.plotter.ren_win.SetMultiSamples(0)
        except Exception:
            pass
        self.plotter.show_axes()

        self._populate_zone_combo([])
        self._populate_scalar_combo([])

    def _build_widgets(self) -> None:
        root = QWidget()
        self.root = root
        self.setCentralWidget(root)

        self.btn_open = QPushButton("Open…")
        self.btn_clear = QPushButton("Clear")

        self.zone_combo = QComboBox()
        self.zone_combo.setMinimumWidth(320)

        self.scalar_combo = QComboBox()
        self.scalar_combo.setMinimumWidth(220)

        self.view_combo = QComboBox()
        self.view_combo.setMinimumWidth(170)
        self.view_combo.addItems(CameraService.view_presets())

        self.btn_apply_view = QPushButton("Apply view")
        self.btn_screenshot = QPushButton("Screenshot…")

        self.info = QLabel("No file loaded.")
        self.info.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.lbl_zone = QLabel("Zone:")
        self.lbl_scalar = QLabel("Scalar:")
        self.lbl_view = QLabel("View:")

        self.plotter = QtInteractor(root)

    def _build_toolbar_layout(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(8)

        bar.addWidget(self.btn_open)
        bar.addWidget(self.btn_clear)
        bar.addWidget(self.lbl_zone)
        bar.addWidget(self.zone_combo)
        bar.addWidget(self.lbl_scalar)
        bar.addWidget(self.scalar_combo)
        bar.addWidget(self.lbl_view)
        bar.addWidget(self.view_combo)
        bar.addWidget(self.btn_apply_view)
        bar.addWidget(self.btn_screenshot)
        bar.addStretch(1)
        bar.addWidget(self.info)
        return bar

    def _build_main_layout(self) -> None:
        main = QVBoxLayout(self.root)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(8)

        main.addLayout(self._build_toolbar_layout())
        main.addWidget(self.plotter.interactor)

    def _connect_signals(self) -> None:
        self.btn_open.clicked.connect(self.open_file)
        self.btn_clear.clicked.connect(self.clear_scene)
        self.zone_combo.currentIndexChanged.connect(self.on_zone_changed)
        self.scalar_combo.currentIndexChanged.connect(self.on_scalar_changed)
        self.btn_apply_view.clicked.connect(self.apply_view_preset)
        self.btn_screenshot.clicked.connect(self.save_screenshot)

    def open_file(self) -> None:
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

        self._populate_zone_combo(self.state.zones)
        self.zone_combo.setCurrentIndex(0)

    def _populate_zone_combo(self, zones: list[ZoneItem]) -> None:
        self.zone_combo.blockSignals(True)
        self.zone_combo.clear()
        if not zones:
            self.zone_combo.addItem("(none)")
        else:
            self.zone_combo.addItem("ALL ZONES")
            for zone in zones:
                self.zone_combo.addItem(zone.label)
        self.zone_combo.blockSignals(False)

    def _populate_scalar_combo(self, scalar_names: list[str]) -> None:
        self.scalar_combo.blockSignals(True)
        self.scalar_combo.clear()
        self.scalar_combo.addItem("(none)")
        for name in scalar_names:
            self.scalar_combo.addItem(name)
        self.scalar_combo.blockSignals(False)

    def on_zone_changed(self, idx: int) -> None:
        if not self.state.zones:
            return

        current_scalar_text = self.scalar_combo.currentText()
        self.state.active_indices = ZoneService.select_active_indices(self.state.zones, idx)
        scalar_names = ZoneService.scalar_names_for_active(self.state)
        self.state.active_scalar = ZoneService.derive_active_scalar(scalar_names, current_scalar_text)

        self._populate_scalar_combo(scalar_names)
        scalar_idx = self.scalar_combo.findText(self.state.active_scalar, Qt.MatchExactly)
        self.scalar_combo.setCurrentIndex(scalar_idx if scalar_idx >= 0 else 0)

        self._render()

        self.view_combo.setCurrentText("Isometric")
        self.apply_view_preset()

    def on_scalar_changed(self, idx: int) -> None:
        if not self.state.zones or not self.state.active_indices:
            return

        current_text = self.scalar_combo.itemText(idx) if idx >= 0 else self.scalar_combo.currentText()
        scalar_names = ZoneService.scalar_names_for_active(self.state)
        self.state.active_scalar = ZoneService.derive_active_scalar(scalar_names, current_text)

        scalar_idx = self.scalar_combo.findText(self.state.active_scalar, Qt.MatchExactly)
        self.scalar_combo.blockSignals(True)
        self.scalar_combo.setCurrentIndex(scalar_idx if scalar_idx >= 0 else 0)
        self.scalar_combo.blockSignals(False)

        self._render()

    def _render(self) -> None:
        RenderService.render(self.plotter, self.state)
        self.info.setText(InfoPresenter.build_info_text(self.state))

    def apply_view_preset(self) -> None:
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

    def clear_scene(self) -> None:
        self.state = ViewerState()
        self._loaded = None

        self.plotter.clear()
        self.plotter.show_axes()
        self.plotter.reset_camera()
        self.plotter.render()

        self._populate_zone_combo([])
        self._populate_scalar_combo([])
        self.info.setText("No file loaded.")

    def save_screenshot(self) -> None:
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
