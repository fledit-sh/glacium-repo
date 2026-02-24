from __future__ import annotations

from .sceneinfo import SceneInfoService
from .viewerstate import ViewerState


class InfoPresenter:
    @staticmethod
    def build_info_text(state: ViewerState) -> str:
        if not state.zones or not state.active_indices:
            return "No file loaded."

        datasets = [state.zones[i].dataset for i in state.active_indices]
        zone_labels = [zone.label for zone in state.zones]
        zone_text = SceneInfoService.zone_label(zone_labels, state.active_indices)
        total_pts, total_cells = SceneInfoService.sum_points_and_cells(datasets)
        file_txt = state.path.name if state.path else "<memory>"

        return SceneInfoService.build_label_text(
            file_name=file_txt,
            zone_label=zone_text,
            total_points=total_pts,
            total_cells=total_cells,
            scalar_name=state.active_scalar,
        )
