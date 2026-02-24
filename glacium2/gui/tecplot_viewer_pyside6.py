# tecplot_viewer_pyside6.py
# pip install pyside6 pyvista pyvistaqt vtk
#
# Features:
# - Open Tecplot/VTK mesh via pyvista.read
# - Zone dropdown (MultiBlock -> flattened blocks) + "All zones"
# - Scalar dropdown (point/cell arrays) per zone
# - View presets for reproducible screenshots
# - Screenshot export
#
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import pyvista as pv
from pyvistaqt import QtInteractor

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


VIEW_PRESET_VECTORS: dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]] = {
    "Isometric": ((1.0, 1.0, 1.0), (0.0, 0.0, 1.0)),
    "+X (Right)": ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    "-X (Left)": ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    "+Y (Front)": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    "-Y (Back)": ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
    "+Z (Top)": ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    "-Z (Bottom)": ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
}


@dataclass(frozen=True)
class ZoneItem:
    label: str
    dataset: pv.DataSet


@dataclass
class ViewerState:
    path: Optional[Path] = None
    zones: List[ZoneItem] = field(default_factory=list)
    active_indices: List[int] = field(default_factory=list)
    active_scalar: Optional[str] = None


class ZoneService:
    @staticmethod
    def extract_zones(obj) -> List[ZoneItem]:
        zones: List[ZoneItem] = []
        for i, (label, ds) in enumerate(_iter_datasets_with_labels(obj)):
            pts = getattr(ds, "n_points", 0)
            cells = getattr(ds, "n_cells", 0)
            txt = f"{i:03d} | {label} (pts={pts}, cells={cells})"
            zones.append(ZoneItem(label=txt, dataset=ds))
        return zones

    @staticmethod
    def scalar_names_for_active(state: ViewerState) -> List[str]:
        names: List[str] = []
        for idx in state.active_indices:
            for name in _all_scalar_names(state.zones[idx].dataset):
                if name not in names:
                    names.append(name)
        return names


class RenderService:
    @staticmethod
    def render(plotter: QtInteractor, state: ViewerState) -> None:
        if not state.zones or not state.active_indices:
            return

        plotter.clear()
        plotter.show_axes()
        try:
            plotter.remove_scalar_bar()
        except Exception:
            pass

        scalar = state.active_scalar
        for idx in state.active_indices:
            ds = state.zones[idx].dataset
            has_scalar = scalar and (scalar in ds.point_data or scalar in ds.cell_data)
            kwargs = {"scalars": scalar} if has_scalar else {}
            plotter.add_mesh(ds, show_edges=False, **kwargs)

        if scalar:
            plotter.add_scalar_bar(title=scalar, interactive=False)
        plotter.reset_camera()
        plotter.render()


def select_active_indices(zones: List[ZoneItem], combo_index: int) -> list[int]:
    """Given non-empty zones, return selected indices: all for index<=0, else one shifted by -1."""
    if not zones:
        return []
    if combo_index <= 0:
        return list(range(len(zones)))
    zone_idx = combo_index - 1
    if zone_idx >= len(zones):
        return []
    return [zone_idx]


def derive_active_scalar(scalar_names: List[str], current_text: str) -> Optional[str]:
    """Return the active scalar from current_text when valid, otherwise first available, else None."""
    if current_text != "(none)" and current_text in scalar_names:
        return current_text
    return scalar_names[0] if scalar_names else None


def _iter_datasets_with_labels(obj, prefix: str = "") -> Iterable[Tuple[str, pv.DataSet]]:
    """Flatten MultiBlock recursively, yield (label, dataset)."""
    if isinstance(obj, pv.MultiBlock):
        keys = list(obj.keys()) if hasattr(obj, "keys") else []
        if keys:
            for k in keys:
                b = obj.get(k)
                if b is None:
                    continue
                name = f"{prefix}{k}"
                yield from _iter_datasets_with_labels(b, prefix=name + " / ")
        else:
            for i, b in enumerate(obj):
                if b is None:
                    continue
                name = f"{prefix}block[{i}]"
                yield from _iter_datasets_with_labels(b, prefix=name + " / ")
        return

    ds = obj
    if ds is None:
        return

    pts = getattr(ds, "n_points", 0)
    cells = getattr(ds, "n_cells", 0)
    if pts == 0 and cells == 0:
        return

    label = prefix[:-3] if prefix.endswith(" / ") else (prefix or "dataset")
    yield (label, ds)


def _all_scalar_names(ds: pv.DataSet) -> List[str]:
    names: List[str] = []
    try:
        names.extend(list(ds.point_data.keys()))
    except Exception:
        pass
    try:
        for n in list(ds.cell_data.keys()):
            if n not in names:
                names.append(n)
    except Exception:
        pass
    return names


def _bounds_union(datasets: List[pv.DataSet]) -> Tuple[float, float, float, float, float, float]:
    if not datasets:
        return (0, 1, 0, 1, 0, 1)
    xmin, xmax, ymin, ymax, zmin, zmax = datasets[0].bounds
    for ds in datasets[1:]:
        b = ds.bounds
        xmin = min(xmin, b[0])
        xmax = max(xmax, b[1])
        ymin = min(ymin, b[2])
        ymax = max(ymax, b[3])
        zmin = min(zmin, b[4])
        zmax = max(zmax, b[5])
    return (xmin, xmax, ymin, ymax, zmin, zmax)


def compute_scene_center(bounds: Tuple[float, float, float, float, float, float]) -> Tuple[float, float, float]:
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    return (0.5 * (xmin + xmax), 0.5 * (ymin + ymax), 0.5 * (zmin + zmax))


def compute_camera_radius(bounds: Tuple[float, float, float, float, float, float], factor: float = 1.8) -> float:
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    dx = max(xmax - xmin, 1e-9)
    dy = max(ymax - ymin, 1e-9)
    dz = max(zmax - zmin, 1e-9)
    return factor * max(dx, dy, dz)


def camera_from_preset(
    center: Tuple[float, float, float], radius: float, preset_name: str
) -> Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]]:
    preset = VIEW_PRESET_VECTORS.get(preset_name)
    if preset is None:
        return None

    direction, up = preset
    cx, cy, cz = center
    dx, dy, dz = direction
    position = (cx + radius * dx, cy + radius * dy, cz + radius * dz)
    return (position, center, up)


class TecplotViewer(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tecplot Viewer (PySide6 + PyVistaQt)")
        self.resize(1300, 850)

        # initialize state
        self.state = ViewerState()
        self._loaded: pv.DataSet | pv.MultiBlock | None = None

        # build UI
        self._build_widgets()
        self._build_main_layout()
        self._connect_signals()

        # initialize plotter
        self.plotter.set_background("white")
        try:
            self.plotter.ren_win.SetMultiSamples(0)  # avoid MSAA/FBO issues
        except Exception:
            pass
        self.plotter.show_axes()

        # initialize combos
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
        self.view_combo.addItems(
            [
                "Isometric",
                "+X (Right)",
                "-X (Left)",
                "+Y (Front)",
                "-Y (Back)",
                "+Z (Top)",
                "-Z (Bottom)",
            ]
        )

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
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Tecplot / VTK / Mesh File",
            "",
            "Tecplot/VTK/Mesh (*.dat *.plt *.vtk *.vtu *.vtp *.stl *.obj *.ply);;All Files (*.*)",
        )
        if not path:
            return

        try:
            obj = pv.read(path)
        except Exception as e:
            QMessageBox.critical(self, "Load error", f"Failed to read:\n{path}\n\n{e}")
            return

        self._loaded = obj
        self.state.path = Path(path)
        self.state.zones = ZoneService.extract_zones(obj)
        if not self.state.zones:
            QMessageBox.critical(self, "Load error", "No renderable zones/datasets found in file.")
            return

        self._populate_zone_combo(self.state.zones)
        self.zone_combo.setCurrentIndex(0)

    def _populate_zone_combo(self, zones: List[ZoneItem]) -> None:
        self.zone_combo.blockSignals(True)
        self.zone_combo.clear()
        if not zones:
            self.zone_combo.addItem("(none)")
        else:
            self.zone_combo.addItem("ALL ZONES")
            for z in zones:
                self.zone_combo.addItem(z.label)
        self.zone_combo.blockSignals(False)

    def _populate_scalar_combo(self, scalar_names: List[str]) -> None:
        self.scalar_combo.blockSignals(True)
        self.scalar_combo.clear()
        self.scalar_combo.addItem("(none)")
        for n in scalar_names:
            self.scalar_combo.addItem(n)
        self.scalar_combo.blockSignals(False)

    def on_zone_changed(self, idx: int) -> None:
        if not self.state.zones:
            return

        current_scalar_text = self.scalar_combo.currentText()
        active_indices = select_active_indices(self.state.zones, idx)

        # update state
        self.state.active_indices = active_indices
        scalar_names = ZoneService.scalar_names_for_active(self.state)
        self.state.active_scalar = derive_active_scalar(scalar_names, current_scalar_text)

        # sync combo selection
        self._populate_scalar_combo(scalar_names)
        scalar_idx = self.scalar_combo.findText(self.state.active_scalar, Qt.MatchExactly)
        self.scalar_combo.setCurrentIndex(scalar_idx if scalar_idx >= 0 else 0)

        # render
        self._render()

        # apply camera preset
        self.view_combo.setCurrentText("Isometric")
        self.apply_view_preset()

    def on_scalar_changed(self, idx: int) -> None:
        if not self.state.zones or not self.state.active_indices:
            return

        current_text = self.scalar_combo.itemText(idx) if idx >= 0 else self.scalar_combo.currentText()
        scalar_names = ZoneService.scalar_names_for_active(self.state)

        # update state
        self.state.active_scalar = derive_active_scalar(scalar_names, current_text)

        # sync combo selection
        scalar_idx = self.scalar_combo.findText(self.state.active_scalar, Qt.MatchExactly)
        self.scalar_combo.blockSignals(True)
        self.scalar_combo.setCurrentIndex(scalar_idx if scalar_idx >= 0 else 0)
        self.scalar_combo.blockSignals(False)

        # render
        self._render()

    def _render(self) -> None:
        RenderService.render(self.plotter, self.state)
        self._update_info()

    def _update_info(self) -> None:
        if not self.state.zones or not self.state.active_indices:
            return

        datasets = [self.state.zones[i].dataset for i in self.state.active_indices]
        total_pts = sum(getattr(ds, "n_points", 0) for ds in datasets)
        total_cells = sum(getattr(ds, "n_cells", 0) for ds in datasets)
        zone_txt = "ALL" if len(self.state.active_indices) > 1 else self.state.zones[self.state.active_indices[0]].label
        file_txt = self.state.path.name if self.state.path else "<memory>"
        scalar = self.state.active_scalar or "—"
        self.info.setText(f"{file_txt} | zone={zone_txt} | points={total_pts} cells={total_cells} | scalar={scalar}")

    def apply_view_preset(self) -> None:
        if not self.state.zones or not self.state.active_indices:
            return

        datasets = [self.state.zones[i].dataset for i in self.state.active_indices]
        bounds = _bounds_union(datasets)
        center = compute_scene_center(bounds)
        radius = compute_camera_radius(bounds)
        camera_tuple = camera_from_preset(center, radius, self.view_combo.currentText())
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
            QMessageBox.information(self, "Screenshot", "Nothing to screenshot.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            "screenshot.png",
            "PNG (*.png);;JPG (*.jpg *.jpeg);;All Files (*.*)",
        )
        if not path:
            return

        try:
            self.plotter.screenshot(path)
        except Exception as e:
            QMessageBox.critical(self, "Screenshot error", f"Failed to save screenshot:\n{path}\n\n{e}")


def main() -> int:
    pv.global_theme.window_size = [1300, 850]
    pv.global_theme.smooth_shading = True

    app = QApplication(sys.argv)
    w = TecplotViewer()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
