from __future__ import annotations

from typing import Any, Iterable

from .viewerstate import ZoneItem


class ZoneService:
    """Pure zone utilities: flatten nested containers and select active indices."""

    @staticmethod
    def extract_zones(obj: Any) -> list[ZoneItem]:
        zones: list[ZoneItem] = []
        for i, (label, dataset) in enumerate(ZoneService.walk(obj)):
            pts = int(getattr(dataset, "n_points", 0) or 0)
            cells = int(getattr(dataset, "n_cells", 0) or 0)
            txt = f"{i:03d} | {label} (pts={pts}, cells={cells})"
            zones.append(ZoneItem(label=txt, dataset=dataset))
        return zones

    @staticmethod
    def walk(obj: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
        if ZoneService._looks_like_multiblock(obj):
            keys = list(obj.keys()) if hasattr(obj, "keys") else []
            if keys:
                for key in keys:
                    block = obj.get(key)
                    if block is None:
                        continue
                    name = f"{prefix}{key}"
                    yield from ZoneService.walk(block, prefix=name + " / ")
            else:
                for i, block in enumerate(obj):
                    if block is None:
                        continue
                    name = f"{prefix}block[{i}]"
                    yield from ZoneService.walk(block, prefix=name + " / ")
            return

        points = int(getattr(obj, "n_points", 0) or 0)
        cells = int(getattr(obj, "n_cells", 0) or 0)
        if points == 0 and cells == 0:
            return

        label = prefix[:-3] if prefix.endswith(" / ") else (prefix or "dataset")
        yield (label, obj)

    @staticmethod
    def select_active_indices(zones: list[ZoneItem], combo_index: int) -> list[int]:
        if not zones:
            return []
        if combo_index <= 0:
            return list(range(len(zones)))
        zone_idx = combo_index - 1
        if zone_idx >= len(zones):
            return []
        return [zone_idx]

    @staticmethod
    def _looks_like_multiblock(obj: Any) -> bool:
        has_keys = hasattr(obj, "keys") and callable(getattr(obj, "keys"))
        has_iter = hasattr(obj, "__iter__")
        has_get = hasattr(obj, "get")
        return (has_keys and has_get) or (has_iter and has_get)
