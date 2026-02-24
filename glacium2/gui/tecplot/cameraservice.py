from __future__ import annotations

from typing import Iterable


class CameraService:
    VIEW_PRESET_VECTORS: dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]] = {
        "Isometric": ((1.0, 1.0, 1.0), (0.0, 0.0, 1.0)),
        "+X (Right)": ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        "-X (Left)": ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        "+Y (Front)": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        "-Y (Back)": ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
        "+Z (Top)": ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
        "-Z (Bottom)": ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
    }

    @staticmethod
    def view_presets() -> list[str]:
        return list(CameraService.VIEW_PRESET_VECTORS.keys())

    @staticmethod
    def bounds_union(bounds_list: Iterable[tuple[float, float, float, float, float, float]]) -> tuple[float, float, float, float, float, float]:
        bounds_list = list(bounds_list)
        if not bounds_list:
            return (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)

        xmin, xmax, ymin, ymax, zmin, zmax = bounds_list[0]
        for b in bounds_list[1:]:
            xmin = min(xmin, b[0])
            xmax = max(xmax, b[1])
            ymin = min(ymin, b[2])
            ymax = max(ymax, b[3])
            zmin = min(zmin, b[4])
            zmax = max(zmax, b[5])
        return (xmin, xmax, ymin, ymax, zmin, zmax)

    @staticmethod
    def scene_center(bounds: tuple[float, float, float, float, float, float]) -> tuple[float, float, float]:
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        return (0.5 * (xmin + xmax), 0.5 * (ymin + ymax), 0.5 * (zmin + zmax))

    @staticmethod
    def camera_radius(bounds: tuple[float, float, float, float, float, float], factor: float = 1.8) -> float:
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        dx = max(xmax - xmin, 1e-9)
        dy = max(ymax - ymin, 1e-9)
        dz = max(zmax - zmin, 1e-9)
        return factor * max(dx, dy, dz)

    @staticmethod
    def camera_from_preset(
        center: tuple[float, float, float], radius: float, preset_name: str
    ) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]] | None:
        preset = CameraService.VIEW_PRESET_VECTORS.get(preset_name)
        if preset is None:
            return None

        direction, up = preset
        cx, cy, cz = center
        dx, dy, dz = direction
        position = (cx + radius * dx, cy + radius * dy, cz + radius * dz)
        return (position, center, up)
