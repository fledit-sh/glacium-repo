from __future__ import annotations

from typing import Any

from .viewerstate import ViewerState


class ScalarService:
    """Pure scalar selection rules for active zones."""

    @staticmethod
    def collect_names(dataset: Any) -> list[str]:
        names: list[str] = []
        for container_name in ("point_data", "cell_data"):
            try:
                data = getattr(dataset, container_name)
                for name in list(data.keys()):
                    if name not in names:
                        names.append(str(name))
            except Exception:
                continue
        return names

    @staticmethod
    def scalar_names_for_active(state: ViewerState) -> list[str]:
        names: list[str] = []
        for idx in state.active_indices:
            for name in ScalarService.collect_names(state.zones[idx].dataset):
                if name not in names:
                    names.append(name)
        return names

    @staticmethod
    def derive_active_scalar(scalar_names: list[str], current_text: str) -> str | None:
        if current_text != "(none)" and current_text in scalar_names:
            return current_text
        return scalar_names[0] if scalar_names else None
