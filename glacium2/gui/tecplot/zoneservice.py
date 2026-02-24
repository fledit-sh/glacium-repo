from __future__ import annotations

from typing import Iterable

import pyvista as pv

from .viewerstate import ViewerState, ZoneItem


class ZoneDatasetCatalog:
    """External integration points: collect() and walk() provide renderable datasets."""

    def collect(self, obj: pv.DataSet | pv.MultiBlock) -> list[ZoneItem]:
        zones: list[ZoneItem] = []
        for i, (label, dataset) in enumerate(self.walk(obj)):
            pts = getattr(dataset, "n_points", 0)
            cells = getattr(dataset, "n_cells", 0)
            txt = f"{i:03d} | {label} (pts={pts}, cells={cells})"
            zones.append(ZoneItem(label=txt, dataset=dataset))
        return zones

    def walk(self, obj: pv.DataSet | pv.MultiBlock, prefix: str = "") -> Iterable[tuple[str, pv.DataSet]]:
        if isinstance(obj, pv.MultiBlock):
            keys = list(obj.keys()) if hasattr(obj, "keys") else []
            if keys:
                for key in keys:
                    block = obj.get(key)
                    if block is None:
                        continue
                    name = f"{prefix}{key}"
                    yield from self.walk(block, prefix=name + " / ")
            else:
                for i, block in enumerate(obj):
                    if block is None:
                        continue
                    name = f"{prefix}block[{i}]"
                    yield from self.walk(block, prefix=name + " / ")
            return

        points = getattr(obj, "n_points", 0)
        cells = getattr(obj, "n_cells", 0)
        if points == 0 and cells == 0:
            return

        label = prefix[:-3] if prefix.endswith(" / ") else (prefix or "dataset")
        yield (label, obj)


class ScalarCatalog:
    """External integration point: collect() extracts scalar names from a dataset."""

    def collect(self, dataset: pv.DataSet) -> list[str]:
        names: list[str] = []
        try:
            names.extend(list(dataset.point_data.keys()))
        except Exception:
            pass

        try:
            for name in list(dataset.cell_data.keys()):
                if name not in names:
                    names.append(name)
        except Exception:
            pass
        return names


class ZoneService:
    dataset_catalog = ZoneDatasetCatalog()
    scalar_catalog = ScalarCatalog()

    @staticmethod
    def extract_zones(obj: pv.DataSet | pv.MultiBlock) -> list[ZoneItem]:
        return ZoneService.dataset_catalog.collect(obj)

    @staticmethod
    def scalar_names_for_active(state: ViewerState) -> list[str]:
        names: list[str] = []
        for idx in state.active_indices:
            for name in ZoneService.scalar_catalog.collect(state.zones[idx].dataset):
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
    def derive(scalar_names: list[str], current_text: str) -> str | None:
        if current_text != "(none)" and current_text in scalar_names:
            return current_text
        return scalar_names[0] if scalar_names else None
