from __future__ import annotations

from typing import Any

from pyvistaqt import QtInteractor

from .plotterport import PlotterPort


class PyVistaPlotter(PlotterPort):
    def __init__(self, parent) -> None:
        self._plotter = QtInteractor(parent)

    @property
    def widget(self) -> Any:
        return self._plotter.interactor

    def clear(self) -> None:
        self._plotter.clear()

    def add(self, dataset: Any, scalar: str | None = None) -> None:
        kwargs = {"scalars": scalar} if scalar else {}
        self._plotter.add_mesh(dataset, show_edges=False, **kwargs)

    def axes(self) -> None:
        self._plotter.show_axes()

    def bar(self, title: str | None = None) -> None:
        if title:
            self._plotter.add_scalar_bar(title=title, interactive=False)
            return
        try:
            self._plotter.remove_scalar_bar()
        except Exception:
            pass

    def camera(self, camera_position: Any) -> None:
        self._plotter.camera_position = camera_position

    def render(self) -> None:
        self._plotter.render()

    def shot(self, path: str) -> None:
        self._plotter.screenshot(path)

    def setup(self) -> None:
        self._plotter.set_background("white")
        try:
            self._plotter.ren_win.SetMultiSamples(0)
        except Exception:
            pass
        self.axes()
