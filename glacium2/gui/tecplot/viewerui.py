from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .cameraservice import CameraService
from .viewerstate import ZoneItem


class ViewerUiBuilder:
    """External integration points: build() and bind() wire the viewer shell."""

    def build(self, viewer, plotter) -> None:
        root = QWidget()
        viewer.root = root
        viewer.setCentralWidget(root)

        viewer.btn_open = QPushButton("Open…")
        viewer.btn_clear = QPushButton("Clear")

        viewer.zone_combo = QComboBox()
        viewer.zone_combo.setMinimumWidth(320)

        viewer.scalar_combo = QComboBox()
        viewer.scalar_combo.setMinimumWidth(220)

        viewer.view_combo = QComboBox()
        viewer.view_combo.setMinimumWidth(170)
        viewer.view_combo.addItems(CameraService.view_presets())

        viewer.btn_apply_view = QPushButton("Apply view")
        viewer.btn_screenshot = QPushButton("Screenshot…")

        viewer.info = QLabel("No file loaded.")
        viewer.info.setTextInteractionFlags(Qt.TextSelectableByMouse)

        viewer.lbl_zone = QLabel("Zone:")
        viewer.lbl_scalar = QLabel("Scalar:")
        viewer.lbl_view = QLabel("View:")

        viewer.plotter = plotter
        self.build_layout(viewer)

    def build_toolbar(self, viewer) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(8)

        bar.addWidget(viewer.btn_open)
        bar.addWidget(viewer.btn_clear)
        bar.addWidget(viewer.lbl_zone)
        bar.addWidget(viewer.zone_combo)
        bar.addWidget(viewer.lbl_scalar)
        bar.addWidget(viewer.scalar_combo)
        bar.addWidget(viewer.lbl_view)
        bar.addWidget(viewer.view_combo)
        bar.addWidget(viewer.btn_apply_view)
        bar.addWidget(viewer.btn_screenshot)
        bar.addStretch(1)
        bar.addWidget(viewer.info)
        return bar

    def build_layout(self, viewer) -> None:
        main = QVBoxLayout(viewer.root)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(8)

        main.addLayout(self.build_toolbar(viewer))
        main.addWidget(viewer.plotter.widget)

    def bind(self, viewer) -> None:
        self.bind_signal(viewer.btn_open.clicked, viewer.open)
        self.bind_signal(viewer.btn_clear.clicked, viewer.clear)
        self.bind_signal(viewer.zone_combo.currentIndexChanged, viewer.select)
        self.bind_signal(viewer.scalar_combo.currentIndexChanged, viewer.scalar)
        self.bind_signal(viewer.btn_apply_view.clicked, viewer.apply)
        self.bind_signal(viewer.btn_screenshot.clicked, viewer.save)

    def bind_signal(self, signal, callback: Callable) -> None:
        signal.connect(callback)


class ComboLoader:
    """External integration points: load_zone_options() and load_scalar_options()."""

    def load_zone_options(self, combo: QComboBox, zones: list[ZoneItem]) -> None:
        combo.blockSignals(True)
        combo.clear()
        if not zones:
            combo.addItem("(none)")
        else:
            combo.addItem("ALL ZONES")
            for zone in zones:
                combo.addItem(zone.label)
        combo.blockSignals(False)

    def load_scalar_options(self, combo: QComboBox, scalar_names: list[str]) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("(none)")
        for name in scalar_names:
            combo.addItem(name)
        combo.blockSignals(False)


class ScenePresenter:
    """External integration point: render() refreshes plot + info text."""

    def render(self, plotter, state, info_label: QLabel, render_service, info_presenter) -> None:
        render_service.render(plotter, state)
        info_label.setText(info_presenter.build_info_text(state))
