"""glacium.models.config – tolerant Flat-Config with Extras + helper methods"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml

__all__ = ["GlobalConfig"]


@dataclass
class GlobalConfig:
    """Kernfelder + beliebige Extra-Keys (alle CAPS)."""

    project_uid: str = ""
    base_dir: Path   = Path(".")
    recipe: str      = "prep"
    extras: Dict[str, Any] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------
    def __init__(self, **data: Any):
        caps = {k.upper(): v for k, v in data.items()}
        self.project_uid = caps.pop("PROJECT_UID", "")
        base_val         = caps.pop("BASE_DIR", ".") or "."
        self.base_dir    = Path(base_val)
        self.recipe      = caps.pop("RECIPE", "prep") or "prep"
        self.extras      = caps

    # ------------------------------------------------------------------
    # Dict/Attr API
    # ------------------------------------------------------------------
    def __getitem__(self, key):
        return self.extras[key.upper()]

    def __setitem__(self, key, val):
        self.extras[key.upper()] = val

    def __getattr__(self, item):
        try:
            return self.extras[item.upper()]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __contains__(self, item):
        return item.upper() in self.extras

    def get(self, key: str, default: Any = None) -> Any:
        """dict-esque get – vermeidet AttributeError bei fehlenden Schlüsseln."""
        return self.extras.get(key.upper(), default)

    # ------------------------------------------------------------------
    # YAML I/O
    # ------------------------------------------------------------------
    @classmethod
    def load(cls, file: Path) -> "GlobalConfig":
        data = yaml.safe_load(file.read_text()) if file.exists() else {}
        return cls(**(data or {}))

    def dump(self, file: Path) -> None:
        out = {**self.extras,
               "PROJECT_UID": self.project_uid,
               "BASE_DIR":    str(self.base_dir),
               "RECIPE":      self.recipe}
        file.write_text(yaml.dump(out, sort_keys=False))
