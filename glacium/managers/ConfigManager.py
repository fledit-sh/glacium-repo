"""glacium.managers.config_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Knotenpunkt für *alle* YAML‑Operationen.

Design‑Pattern Map
===================
* **Facade**           – externe Aufrufer sehen nur `ConfigManager`‑Methoden,
  nie rohes *yaml*‑Gefrickel.
* **Strategy**         – Serializer austauschbar (`yaml`, `json`, …).
* **Flyweight**        – `GlobalConfig` & Subsets liegen einmal im Cache.
* **Observer**         – `on_change`‑Hooks, damit andere Manager (Template,
  Job) auf Änderungen reagieren können.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Literal

import yaml

from glacium.managers.PathManager import PathManager
from glacium.models.config import GlobalConfig  # type: ignore

__all__ = ["ConfigManager"]


# ────────────────────────────────────────────────────────────────────────────────
#  Serializer‑Strategien
# ────────────────────────────────────────────────────────────────────────────────
class _YamlSerializer:
    ext = ".yaml"

    @staticmethod
    def load(path: Path) -> Dict[str, Any]:
        return yaml.safe_load(path.read_text()) or {}

    @staticmethod
    def dump(data: Dict[str, Any], path: Path) -> None:
        path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")


class _JsonSerializer:
    ext = ".json"

    @staticmethod
    def load(path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text())

    @staticmethod
    def dump(data: Dict[str, Any], path: Path) -> None:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")


_SERIALIZERS: Dict[str, Any] = {
    "yaml": _YamlSerializer,
    "json": _JsonSerializer,
}


# ────────────────────────────────────────────────────────────────────────────────
#  Main Facade
# ────────────────────────────────────────────────────────────────────────────────
class ConfigManager:
    """Zentraler YAML‑Loader / ‑Schreiber mit Cache & Merge‑Utilities."""

    def __init__(self, paths: PathManager, *, fmt: Literal["yaml", "json"] = "yaml"):
        self.paths = paths
        self.serializer = _SERIALIZERS[fmt]
        self._global: GlobalConfig | None = None
        self._subset_cache: Dict[str, Dict[str, Any]] = {}
        self._observers: List[Callable[[str], None]] = []

    # ------------------------------------------------------------------
    # Observer‑Support
    # ------------------------------------------------------------------
    def add_observer(self, fn: Callable[[str], None]) -> None:
        self._observers.append(fn)

    def _emit(self, event: str) -> None:
        for fn in self._observers:
            fn(event)

    # ------------------------------------------------------------------
    # Load / Dump
    # ------------------------------------------------------------------
    def load_global(self) -> GlobalConfig:
        if self._global is None:
            self._global = GlobalConfig.load(self.paths.global_cfg_file())  # type: ignore[attr-defined]
        return self._global

    def dump_global(self) -> None:
        if self._global is not None:
            self._global.dump(self.paths.global_cfg_file())  # type: ignore[attr-defined]
            self._emit("global_saved")

    def load_subset(self, name: str) -> Dict[str, Any]:
        if name not in self._subset_cache:
            file = self.paths.cfg_dir() / f"{name}{self.serializer.ext}"
            self._subset_cache[name] = self.serializer.load(file)
        return self._subset_cache[name]

    def dump_subset(self, name: str) -> None:
        if name in self._subset_cache:
            file = self.paths.cfg_dir() / f"{name}{self.serializer.ext}"
            self.serializer.dump(self._subset_cache[name], file)
            self._emit(f"subset_saved:{name}")

    # ------------------------------------------------------------------
    # Merge / Split Utilities
    # ------------------------------------------------------------------
    def merge_subsets(self, names: Iterable[str]) -> GlobalConfig:
        """Aktualisiert die globale Config mit Werten aus Teil‑YAMLs
        (Keys, die fehlen, werden **nicht** entfernt)."""
        glb_dict = self.load_global().__dict__.copy()
        for n in names:
            sub = self.load_subset(n)
            glb_dict.update(sub)  # nur simple union – conflict = override
        self._global = GlobalConfig(**glb_dict)  # type: ignore[arg-type]
        self.dump_global()
        return self._global

    def update_subset_from_global(self, name: str) -> None:
        """Überschreibt nur vorhandene Keys im Subset mit Global‑Werten."""
        global_cfg = self.load_global().__dict__
        subset = self.load_subset(name)
        subset.update({k: global_cfg[k] for k in subset.keys() if k in global_cfg})
        self.dump_subset(name)

    def split_all(self) -> None:
        """Geht alle Sub‑Configs durch und ruft *update_subset_from_global*."""
        for file in self.paths.cfg_dir().glob(f"*{self.serializer.ext}"):
            self.update_subset_from_global(file.stem)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def get(self, key: str) -> Any:
        return getattr(self.load_global(), key)

    def set(self, key: str, value: Any) -> None:
        setattr(self.load_global(), key, value)
        self.dump_global()
