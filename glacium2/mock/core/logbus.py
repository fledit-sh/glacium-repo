from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class LogBus(QObject):
    message = Signal(str)
