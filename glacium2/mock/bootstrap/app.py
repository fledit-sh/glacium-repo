from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ..core.registry import Registry
from .panels import make as make_panels
from .services import make as make_services
from .window import build


def run() -> int:
    app = QApplication(sys.argv)
    registry = Registry()
    for spec in make_panels():
        registry.add(spec)

    win = build(registry, make_services())
    win.resize(1300, 800)
    win.show()
    return app.exec()
