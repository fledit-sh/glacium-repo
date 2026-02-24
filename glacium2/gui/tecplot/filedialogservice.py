from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QWidget


class FileDialogService:
    @staticmethod
    def open_mesh_file(parent: QWidget) -> str:
        path, _ = QFileDialog.getOpenFileName(
            parent,
            "Open Tecplot / VTK / Mesh File",
            "",
            "Tecplot/VTK/Mesh (*.dat *.plt *.vtk *.vtu *.vtp *.stl *.obj *.ply);;All Files (*.*)",
        )
        return path

    @staticmethod
    def save_screenshot_file(parent: QWidget) -> str:
        path, _ = QFileDialog.getSaveFileName(
            parent,
            "Save Screenshot",
            "screenshot.png",
            "PNG (*.png);;JPG (*.jpg *.jpeg);;All Files (*.*)",
        )
        return path
