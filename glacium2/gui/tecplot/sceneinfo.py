from __future__ import annotations

from typing import Iterable


class SceneInfoService:
    """Pure aggregation helpers for scene metadata text."""

    @staticmethod
    def sum_points_and_cells(datasets: Iterable[object]) -> tuple[int, int]:
        total_pts = 0
        total_cells = 0
        for ds in datasets:
            total_pts += int(getattr(ds, "n_points", 0) or 0)
            total_cells += int(getattr(ds, "n_cells", 0) or 0)
        return total_pts, total_cells

    @staticmethod
    def zone_label(zone_labels: list[str], active_indices: list[int]) -> str:
        if not zone_labels or not active_indices:
            return "—"
        if len(active_indices) > 1:
            return "ALL"
        idx = active_indices[0]
        if idx < 0 or idx >= len(zone_labels):
            return "—"
        return zone_labels[idx]

    @staticmethod
    def build_label_text(
        file_name: str,
        zone_label: str,
        total_points: int,
        total_cells: int,
        scalar_name: str | None,
    ) -> str:
        scalar = scalar_name or "—"
        return f"{file_name} | zone={zone_label} | points={total_points} cells={total_cells} | scalar={scalar}"
