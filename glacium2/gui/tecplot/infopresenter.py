from __future__ import annotations

from .viewerstate import ViewerState


class InfoPresenter:
    @staticmethod
    def build_info_text(state: ViewerState) -> str:
        if not state.zones or not state.active_indices:
            return "No file loaded."

        datasets = [state.zones[i].dataset for i in state.active_indices]
        zone_text = "ALL" if len(state.active_indices) > 1 else state.zones[state.active_indices[0]].label
        scalar = state.active_scalar or "—"

        total_pts = sum(getattr(ds, "n_points", 0) for ds in datasets)
        total_cells = sum(getattr(ds, "n_cells", 0) for ds in datasets)
        file_txt = state.path.name if state.path else "<memory>"
        return f"{file_txt} | zone={zone_text} | points={total_pts} cells={total_cells} | scalar={scalar}"
