from __future__ import annotations

from pyvistaqt import QtInteractor

from .viewerstate import ViewerState


class RenderService:
    @staticmethod
    def render(plotter: QtInteractor, state: ViewerState) -> None:
        if not state.zones or not state.active_indices:
            return

        plotter.clear()
        plotter.show_axes()
        try:
            plotter.remove_scalar_bar()
        except Exception:
            pass

        scalar = state.active_scalar
        for idx in state.active_indices:
            ds = state.zones[idx].dataset
            has_scalar = scalar and (scalar in ds.point_data or scalar in ds.cell_data)
            kwargs = {"scalars": scalar} if has_scalar else {}
            plotter.add_mesh(ds, show_edges=False, **kwargs)

        if scalar:
            plotter.add_scalar_bar(title=scalar, interactive=False)
        plotter.reset_camera()
        plotter.render()
