from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


class MessageBoxService:
    @staticmethod
    def show_load_error(parent: QWidget, path: str, exc: Exception | str) -> None:
        QMessageBox.critical(parent, "Load error", f"Could not open file.\n{path}\n\n{exc}")

    @staticmethod
    def show_screenshot_error(parent: QWidget, path: str, exc: Exception | str) -> None:
        QMessageBox.critical(parent, "Screenshot error", f"Could not save screenshot.\n{path}\n\n{exc}")

    @staticmethod
    def show_no_screenshot_data(parent: QWidget) -> None:
        QMessageBox.information(parent, "Screenshot", "Nothing to screenshot.")
