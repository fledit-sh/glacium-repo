from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

from .messageport import MessagePort


class QtMessageBox(MessagePort):
    def __init__(self, parent: QWidget) -> None:
        self._parent = parent

    def error(self, title: str, text: str) -> None:
        QMessageBox.critical(self._parent, title, text)

    def info(self, title: str, text: str) -> None:
        QMessageBox.information(self._parent, title, text)
