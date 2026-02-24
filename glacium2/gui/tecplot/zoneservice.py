from __future__ import annotations

from typing import Iterable

import pyvista as pv

from .viewerstate import ViewerState, ZoneItem


class ZoneService:
    @staticmethod
    def extract_zones(obj: pv.DataSet | pv.MultiBlock) -> list[ZoneItem]:
        zones: list[ZoneItem] = []
        for i, (label, ds) in enumerate(_iter_datasets_with_labels(obj)):
            pts = getattr(ds, "n_points", 0)
            cells = getattr(ds, "n_cells", 0)
            txt = f"{i:03d} | {label} (pts={pts}, cells={cells})"
            zones.append(ZoneItem(label=txt, dataset=ds))
        return zones

    @staticmethod
    def scalar_names_for_active(state: ViewerState) -> list[str]:
        names: list[str] = []
        for idx in state.active_indices:
            for name in _all_scalar_names(state.zones[idx].dataset):
                if name not in names:
                    names.append(name)
        return names

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
    def derive_active_scalar(scalar_names: list[str], current_text: str) -> str | None:
        if current_text != "(none)" and current_text in scalar_names:
            return current_text
        return scalar_names[0] if scalar_names else None


def _iter_datasets_with_labels(obj, prefix: str = "") -> Iterable[tuple[str, pv.DataSet]]:
    if isinstance(obj, pv.MultiBlock):
        keys = list(obj.keys()) if hasattr(obj, "keys") else []
        if keys:
            for key in keys:
                block = obj.get(key)
                if block is None:
                    continue
                name = f"{prefix}{key}"
                yield from _iter_datasets_with_labels(block, prefix=name + " / ")
        else:
            for i, block in enumerate(obj):
                if block is None:
                    continue
                name = f"{prefix}block[{i}]"
                yield from _iter_datasets_with_labels(block, prefix=name + " / ")
        return

    ds = obj
    if ds is None:
        return

    pts = getattr(ds, "n_points", 0)
    cells = getattr(ds, "n_cells", 0)
    if pts == 0 and cells == 0:
        return

    label = prefix[:-3] if prefix.endswith(" / ") else (prefix or "dataset")
    yield (label, ds)


def _all_scalar_names(ds: pv.DataSet) -> list[str]:
    names: list[str] = []
    try:
        names.extend(list(ds.point_data.keys()))
    except Exception:
        pass
    try:
        for name in list(ds.cell_data.keys()):
            if name not in names:
                names.append(name)
    except Exception:
        pass
    return names
