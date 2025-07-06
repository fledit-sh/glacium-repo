"""glacium.models.case – dataclass for case configuration."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, ClassVar

import yaml

__all__ = ["CaseConfig"]


@dataclass
class CaseConfig:
    """All parameters describing an icing case."""

    roughness: float = 0.001
    characteristic_length: float = 0.431
    velocity: float = 50.0
    altitude: float = 100.0
    temperature: float = 270.0
    aoa: float = 4.0
    mvd: float = 20.0
    lwc: float = 0.001
    yplus: float = 0.3

    reynolds_number: float | None = None
    ref_area: float | None = None
    moment_x: float | None = None
    moment_y: float | None = None
    moment_z: float | None = None

    # mapping from YAML keys to attribute names
    _KEYMAP: ClassVar[Dict[str, str]] = {
        "CASE_ROUGHNESS": "roughness",
        "CASE_CHARACTERISTIC_LENGTH": "characteristic_length",
        "CASE_VELOCITY": "velocity",
        "CASE_ALTITUDE": "altitude",
        "CASE_TEMPERATURE": "temperature",
        "CASE_AOA": "aoa",
        "CASE_MVD": "mvd",
        "CASE_LWC": "lwc",
        "CASE_YPLUS": "yplus",
        "CASE_REYNOLDSNUMBER": "reynolds_number",
        "CASE_REF_AREA": "ref_area",
        "CASE_MOMENT_X": "moment_x",
        "CASE_MOMENT_Y": "moment_y",
        "CASE_MOMENT_Z": "moment_z",
    }
    _INV_KEYMAP: ClassVar[Dict[str, str]] = {v: k for k, v in _KEYMAP.items()}

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, file: Path) -> "CaseConfig":
        data: Dict[str, Any] = {}
        if file.exists():
            raw = yaml.safe_load(file.read_text()) or {}
            data = {cls._KEYMAP.get(k.upper(), k.lower()): v for k, v in raw.items()}
        return cls(**data)

    # ------------------------------------------------------------------
    def dump(self, file: Path) -> None:
        data = {self._INV_KEYMAP[name]: getattr(self, name) for name in self._INV_KEYMAP}
        file.write_text(yaml.dump(data, sort_keys=False))

