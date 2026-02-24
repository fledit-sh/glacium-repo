from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class ZoneItem:
    label: str
    dataset: Any


@dataclass
class ViewerState:
    path: Optional[Path] = None
    zones: list[ZoneItem] = field(default_factory=list)
    active_indices: list[int] = field(default_factory=list)
    active_scalar: Optional[str] = None
