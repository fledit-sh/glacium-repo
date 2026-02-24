from __future__ import annotations

from .plotterport import PlotterPort
from .viewerstate import ViewerState


class RenderService:
    @staticmethod
    def render(plotter: PlotterPort, state: ViewerState) -> None:
        if not state.zones or not state.active_indices:
            return

        plotter.clear()
        plotter.axes()
        plotter.bar(None)

        scalar = state.active_scalar
        for idx in state.active_indices:
            ds = state.zones[idx].dataset
            has_scalar = scalar and (scalar in ds.point_data or scalar in ds.cell_data)
            plotter.add(ds, scalar if has_scalar else None)

        if scalar:
            plotter.bar(scalar)
        plotter.render()
