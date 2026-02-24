from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QWidget

from .dialogport import DialogPort


class QtFileDialog(DialogPort):
    def __init__(self, parent: QWidget) -> None:
        self._parent = parent

    def open(self) -> str:
        path, _ = QFileDialog.getOpenFileName(
            self._parent,
            "Open Tecplot / VTK / Mesh File",
            "",
            "Tecplot/VTK/Mesh (*.dat *.plt *.vtk *.vtu *.vtp *.stl *.obj *.ply);;All Files (*.*)",
        )
        return path

    def save(self) -> str:
        path, _ = QFileDialog.getSaveFileName(
            self._parent,
            "Save Screenshot",
            "screenshot.png",
            "PNG (*.png);;JPG (*.jpg *.jpeg);;All Files (*.*)",
        )
        return path
