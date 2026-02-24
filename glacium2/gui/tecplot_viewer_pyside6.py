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
from dataclasses import dataclass
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


@dataclass(frozen=True)
class ZoneItem:
    label: str
    dataset: pv.DataSet


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


class TecplotViewer(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tecplot Viewer (PySide6 + PyVistaQt)")
        self.resize(1300, 850)

        self._path: Optional[Path] = None
        self._loaded: pv.DataSet | pv.MultiBlock | None = None
        self._zones: List[ZoneItem] = []
        self._active_indices: List[int] = []
        self._active_scalar: Optional[str] = None

        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(8)

        bar = QHBoxLayout()
        bar.setSpacing(8)

        self.btn_open = QPushButton("Open…")
        self.btn_open.clicked.connect(self.open_file)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_scene)

        self.zone_combo = QComboBox()
        self.zone_combo.setMinimumWidth(320)
        self.zone_combo.currentIndexChanged.connect(self.on_zone_changed)

        self.scalar_combo = QComboBox()
        self.scalar_combo.setMinimumWidth(220)
        self.scalar_combo.currentIndexChanged.connect(self.on_scalar_changed)

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
        self.btn_apply_view.clicked.connect(self.apply_view_preset)

        self.btn_screenshot = QPushButton("Screenshot…")
        self.btn_screenshot.clicked.connect(self.save_screenshot)

        self.info = QLabel("No file loaded.")
        self.info.setTextInteractionFlags(Qt.TextSelectableByMouse)

        bar.addWidget(self.btn_open)
        bar.addWidget(self.btn_clear)
        bar.addWidget(QLabel("Zone:"))
        bar.addWidget(self.zone_combo)
        bar.addWidget(QLabel("Scalar:"))
        bar.addWidget(self.scalar_combo)
        bar.addWidget(QLabel("View:"))
        bar.addWidget(self.view_combo)
        bar.addWidget(self.btn_apply_view)
        bar.addWidget(self.btn_screenshot)
        bar.addStretch(1)
        bar.addWidget(self.info)

        main.addLayout(bar)

        self.plotter = QtInteractor(root)
        main.addWidget(self.plotter.interactor)

        self.plotter.set_background("white")
        try:
            self.plotter.ren_win.SetMultiSamples(0)  # avoid MSAA/FBO issues
        except Exception:
            pass
        self.plotter.show_axes()

        self._populate_zone_combo([])
        self._populate_scalar_combo([])

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

        self._path = Path(path)
        self._loaded = obj
        self._zones = self._extract_zones(obj)
        if not self._zones:
            QMessageBox.critical(self, "Load error", "No renderable zones/datasets found in file.")
            return

        self._populate_zone_combo(self._zones)
        self.zone_combo.setCurrentIndex(0)  # ALL ZONES

    def _extract_zones(self, obj) -> List[ZoneItem]:
        tmp: List[ZoneItem] = []
        for label, ds in _iter_datasets_with_labels(obj):
            pts = getattr(ds, "n_points", 0)
            cells = getattr(ds, "n_cells", 0)
            tmp.append(ZoneItem(label=f"{label} (pts={pts}, cells={cells})", dataset=ds))

        out: List[ZoneItem] = []
        for i, z in enumerate(tmp):
            out.append(ZoneItem(label=f"{i:03d} | {z.label}", dataset=z.dataset))
        return out

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
        if not self._zones:
            return

        if idx <= 0:
            self._active_indices = list(range(len(self._zones)))
        else:
            self._active_indices = [idx - 1]

        scalar_names = self._scalar_names_for_active()
        self._populate_scalar_combo(scalar_names)

        self._active_scalar = scalar_names[0] if scalar_names else None
        if self._active_scalar is None:
            self.scalar_combo.setCurrentIndex(0)
        else:
            j = self.scalar_combo.findText(self._active_scalar, Qt.MatchExactly)
            self.scalar_combo.setCurrentIndex(j if j >= 0 else 0)

        self._render_active()
        self.view_combo.setCurrentText("Isometric")
        self.apply_view_preset()

    def _scalar_names_for_active(self) -> List[str]:
        names: List[str] = []
        for i in self._active_indices:
            ds = self._zones[i].dataset
            for n in _all_scalar_names(ds):
                if n not in names:
                    names.append(n)
        return names

    def on_scalar_changed(self, idx: int) -> None:
        if not self._zones or not self._active_indices:
            return
        txt = self.scalar_combo.currentText()
        self._active_scalar = None if txt == "(none)" else txt
        self._render_active()

    def _render_active(self) -> None:
        if not self._zones or not self._active_indices:
            return

        self.plotter.clear()
        self.plotter.show_axes()

        try:
            self.plotter.remove_scalar_bar()
        except Exception:
            pass

        datasets = [self._zones[i].dataset for i in self._active_indices]
        scalar = self._active_scalar

        for ds in datasets:
            if scalar and (scalar in getattr(ds, "point_data", {}) or scalar in getattr(ds, "cell_data", {})):
                self.plotter.add_mesh(ds, scalars=scalar, show_edges=False)
            else:
                self.plotter.add_mesh(ds, show_edges=False)

        if scalar:
            self.plotter.add_scalar_bar(title=scalar, interactive=False)

        self.plotter.reset_camera()
        self.plotter.render()

        total_pts = sum(getattr(ds, "n_points", 0) for ds in datasets)
        total_cells = sum(getattr(ds, "n_cells", 0) for ds in datasets)
        zone_txt = "ALL" if len(self._active_indices) > 1 else self._zones[self._active_indices[0]].label
        file_txt = self._path.name if self._path else "<memory>"
        self.info.setText(f"{file_txt} | zone={zone_txt} | points={total_pts} cells={total_cells} | scalar={scalar or '—'}")


    def apply_view_preset(self) -> None:
        if not self._zones or not self._active_indices:
            return

        datasets = [self._zones[i].dataset for i in self._active_indices]
        xmin, xmax, ymin, ymax, zmin, zmax = _bounds_union(datasets)

        cx = 0.5 * (xmin + xmax)
        cy = 0.5 * (ymin + ymax)
        cz = 0.5 * (zmin + zmax)
        center = (cx, cy, cz)

        dx = max(xmax - xmin, 1e-9)
        dy = max(ymax - ymin, 1e-9)
        dz = max(zmax - zmin, 1e-9)
        r = 1.8 * max(dx, dy, dz)

        preset = self.view_combo.currentText()

        if preset == "Isometric":
            pos = (cx + r, cy + r, cz + r)
            up = (0, 0, 1)
        elif preset == "+X (Right)":
            pos = (cx + r, cy, cz)
            up = (0, 0, 1)
        elif preset == "-X (Left)":
            pos = (cx - r, cy, cz)
            up = (0, 0, 1)
        elif preset == "+Y (Front)":
            pos = (cx, cy + r, cz)
            up = (0, 0, 1)
        elif preset == "-Y (Back)":
            pos = (cx, cy - r, cz)
            up = (0, 0, 1)
        elif preset == "+Z (Top)":
            pos = (cx, cy, cz + r)
            up = (0, 1, 0)
        elif preset == "-Z (Bottom)":
            pos = (cx, cy, cz - r)
            up = (0, 1, 0)
        else:
            return

        self.plotter.camera_position = [pos, center, up]
        self.plotter.render()

    def clear_scene(self) -> None:
        self._path = None
        self._loaded = None
        self._zones = []
        self._active_indices = []
        self._active_scalar = None

        self.plotter.clear()
        self.plotter.show_axes()
        self.plotter.reset_camera()
        self.plotter.render()

        self._populate_zone_combo([])
        self._populate_scalar_combo([])
        self.info.setText("No file loaded.")

    def save_screenshot(self) -> None:
        if not self._zones or not self._active_indices:
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
