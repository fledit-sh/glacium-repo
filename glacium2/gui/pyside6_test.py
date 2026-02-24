# tecplot_viewer.py
# pip install pyside6 pyvista pyvistaqt vtk

from __future__ import annotations

import sys
from pathlib import Path

import pyvista as pv
from pyvistaqt import QtInteractor

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
def _pick_first_dataset(obj: pv.DataSet | pv.MultiBlock) -> pv.DataSet | None:
    """Return first non-empty DataSet from a MultiBlock (recursive)."""
    if isinstance(obj, pv.MultiBlock):
        for block in obj:
            if block is None:
                continue
            ds = _pick_first_dataset(block)  # recurse (MultiBlock-in-MultiBlock)
            if ds is None:
                continue
            # skip totally empty datasets
            if getattr(ds, "n_points", 0) > 0 or getattr(ds, "n_cells", 0) > 0:
                return ds
        return None
    return obj  # already a DataSet


def _first_scalar_name(ds: pv.DataSet) -> str | None:
    # prefer point scalars
    if hasattr(ds, "point_data") and ds.point_data is not None:
        keys = list(ds.point_data.keys())
        if keys:
            return keys[0]
    # else cell scalars
    if hasattr(ds, "cell_data") and ds.cell_data is not None:
        keys = list(ds.cell_data.keys())
        if keys:
            return keys[0]
    return None

def _iter_datasets(obj):
    import pyvista as pv
    if isinstance(obj, pv.MultiBlock):
        for b in obj:
            if b is None:
                continue
            yield from _iter_datasets(b)
    else:
        yield obj
class TecplotViewer(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tecplot Viewer (PySide6 + PyVistaQt)")
        self.resize(1200, 800)

        self._mesh: pv.DataSet | None = None

        # --- UI
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.btn_open = QPushButton("Open…")
        self.btn_open.clicked.connect(self.open_file)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_scene)

        self.btn_screenshot = QPushButton("Screenshot…")
        self.btn_screenshot.clicked.connect(self.save_screenshot)

        self.info = QLabel("No file loaded.")
        self.info.setTextInteractionFlags(Qt.TextSelectableByMouse)

        toolbar.addWidget(self.btn_open)
        toolbar.addWidget(self.btn_clear)
        toolbar.addWidget(self.btn_screenshot)
        toolbar.addStretch(1)
        toolbar.addWidget(self.info)

        main.addLayout(toolbar)

        # --- 3D View
        self.plotter = QtInteractor(root)
        main.addWidget(self.plotter.interactor)

        # a decent default look
        self.plotter.set_background("white")
        self.plotter.enable_anti_aliasing("ssaa")
        self.plotter.show_axes()

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
            mesh = pv.read(path)
        except Exception as e:
            QMessageBox.critical(self, "Load error", f"Failed to read:\n{path}\n\n{e}")
            return

        self.load_mesh(mesh, Path(path))



    def load_mesh(self, mesh, path=None) -> None:
        self.plotter.clear()

        datasets = [ds for ds in _iter_datasets(mesh) if getattr(ds, "n_points", 0) > 0]
        if not datasets:
            raise RuntimeError("No renderable datasets found.")

        # choose a scalar that exists on the first dataset (simple default)
        scalar_name = _first_scalar_name(datasets[0])

        for ds in datasets:
            if scalar_name and scalar_name in ds.point_data:
                self.plotter.add_mesh(ds, scalars=scalar_name, show_edges=False)
            elif scalar_name and scalar_name in ds.cell_data:
                self.plotter.add_mesh(ds, scalars=scalar_name, show_edges=False)
            else:
                self.plotter.add_mesh(ds, show_edges=False)

        if scalar_name:
            self.plotter.add_scalar_bar(title=scalar_name, interactive=False)

        total_pts = sum(ds.n_points for ds in datasets)
        total_cells = sum(ds.n_cells for ds in datasets)
        self.info.setText(
            f"{path.name if path else '<memory>'} | blocks={len(datasets)} points={total_pts} cells={total_cells} scalars={scalar_name or '—'}"
        )
        self.plotter.reset_camera()

    def clear_scene(self) -> None:
        self._mesh = None
        self.plotter.clear()
        self.plotter.show_axes()
        self.plotter.reset_camera()
        self.info.setText("No file loaded.")

    def save_screenshot(self) -> None:
        if self._mesh is None:
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
            # QtInteractor supports screenshot via the underlying plotter
            self.plotter.screenshot(path)
        except Exception as e:
            QMessageBox.critical(self, "Screenshot error", f"Failed to save screenshot:\n{path}\n\n{e}")
            return


def main() -> int:
    # Optional: nicer rendering defaults for scientific viz
    pv.global_theme.window_size = [1200, 800]
    pv.global_theme.smooth_shading = True

    app = QApplication(sys.argv)
    w = TecplotViewer()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())