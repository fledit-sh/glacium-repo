"""Central access point for project configuration.

The :class:`ConfigManager` hides raw YAML or JSON handling behind a small
Python API.  It keeps the global configuration cached in memory and provides
helpers to load, merge and split configuration subsets.

Design patterns used
--------------------
* **Facade** – all configuration reads and writes go through this manager.
* **Strategy** – the serializer (``yaml`` or ``json``) can be selected.
* **Flyweight** – the :class:`~glacium.models.config.GlobalConfig` instance and
  subset data are cached.
* **Observer** – registered callbacks are triggered whenever data is saved.

Example
-------
>>> from pathlib import Path
>>> from glacium.managers.path_manager import PathBuilder
>>> paths = PathBuilder(Path('runs/my_proj')).build()
>>> mgr = ConfigManager(paths)
>>> cfg = mgr.load_global()
>>> mgr.set('PROJECT_NAME', 'Demo')
>>> mgr.dump_global()
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Literal

import yaml

from glacium.managers.path_manager import PathManager
from glacium.models.config import GlobalConfig  # type: ignore

__all__ = ["ConfigManager"]


# ────────────────────────────────────────────────────────────────────────────────
#  Serializer‑Strategien
# ────────────────────────────────────────────────────────────────────────────────
class _YamlSerializer:
    """Helper strategy to read and write YAML files."""

    ext = ".yaml"

    @staticmethod
    def load(path: Path) -> Dict[str, Any]:
        """Load ``path`` as YAML and return a dictionary."""

        return yaml.safe_load(path.read_text()) or {}

    @staticmethod
    def dump(data: Dict[str, Any], path: Path) -> None:
        """Serialize ``data`` as YAML into ``path``."""

        path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")


class _JsonSerializer:
    """Helper strategy to read and write JSON files."""

    ext = ".json"

    @staticmethod
    def load(path: Path) -> Dict[str, Any]:
        """Return the parsed JSON content of ``path``."""

        return json.loads(path.read_text())

    @staticmethod
    def dump(data: Dict[str, Any], path: Path) -> None:
        """Serialize ``data`` as JSON into ``path``."""

        path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# Map of available serializer strategies.
_SERIALIZERS: Dict[str, Any] = {
    "yaml": _YamlSerializer,
    "json": _JsonSerializer,
}


# ────────────────────────────────────────────────────────────────────────────────
#  Main Facade
# ────────────────────────────────────────────────────────────────────────────────
class ConfigManager:
    """Facade for reading and writing project configuration files.

    The manager lazily loads the global configuration and keeps it cached in
    memory.  Additional subset files can be merged into the global state or
    written back to disk.
    """

    def __init__(self, paths: PathManager, *, fmt: Literal["yaml", "json"] = "yaml"):
        """Initialise the manager.

        Parameters
        ----------
        paths : PathManager
            Object describing all project directories.
        fmt : Literal["yaml", "json"], optional
            Serializer format to use, defaults to ``"yaml"``.
        """

        self.paths = paths
        self.serializer = _SERIALIZERS[fmt]
        self._global: GlobalConfig | None = None
        self._subset_cache: Dict[str, Dict[str, Any]] = {}
        self._observers: List[Callable[[str], None]] = []

    # ------------------------------------------------------------------
    # Observer‑Support
    # ------------------------------------------------------------------
    def add_observer(self, fn: Callable[[str], None]) -> None:
        """Register ``fn`` to be notified when data is saved.

        The callback receives a string describing the event, e.g.
        ``"global_saved"`` or ``"subset_saved:<name>"``.
        """

        self._observers.append(fn)

    def _emit(self, event: str) -> None:
        """Call all registered observers with ``event``."""

        # This helper isolates the observer pattern so other methods simply
        # call ``_emit`` after persisting data.

        for fn in self._observers:
            fn(event)

    # ------------------------------------------------------------------
    # Load / Dump
    # ------------------------------------------------------------------
    def load_global(self) -> GlobalConfig:
        """Return the cached global configuration.

        On the first call the configuration is loaded from the
        ``global_config.yaml`` file located in the project configuration
        directory.  Subsequent calls return the cached object.
        """

        if self._global is None:
            self._global = GlobalConfig.load(self.paths.global_cfg_file())  # type: ignore[attr-defined]
        return self._global

    def dump_global(self) -> None:
        """Persist the global configuration to disk and notify observers."""

        # Only writes when a configuration has been loaded or modified.
        if self._global is not None:
            self._global.dump(self.paths.global_cfg_file())  # type: ignore[attr-defined]
            self._emit("global_saved")

    def load_subset(self, name: str) -> Dict[str, Any]:
        """Load a configuration subset.

        Parameters
        ----------
        name : str
            Name of the subset without file extension.

        Returns
        -------
        dict
            Parsed key/value mapping for the subset.
        """

        if name not in self._subset_cache:
            file = self.paths.cfg_dir() / f"{name}{self.serializer.ext}"
            self._subset_cache[name] = self.serializer.load(file)
        return self._subset_cache[name]

    def dump_subset(self, name: str) -> None:
        """Write a previously loaded subset back to disk."""

        # Only subsets returned by :meth:`load_subset` are cached and can be
        # written safely.
        if name in self._subset_cache:
            file = self.paths.cfg_dir() / f"{name}{self.serializer.ext}"
            self.serializer.dump(self._subset_cache[name], file)
            self._emit(f"subset_saved:{name}")

    # ------------------------------------------------------------------
    # Merge / Split Utilities
    # ------------------------------------------------------------------
    def merge_subsets(self, names: Iterable[str]) -> GlobalConfig:
        """Merge several subsets into the global configuration.

        Parameters
        ----------
        names : Iterable[str]
            Iterable of subset names to merge.

        Returns
        -------
        GlobalConfig
            Updated global configuration instance.
        """
        glb_dict = self.load_global().__dict__.copy()
        for n in names:
            sub = self.load_subset(n)
            glb_dict.update(sub)  # nur simple union – conflict = override
        self._global = GlobalConfig(**glb_dict)  # type: ignore[arg-type]
        self.dump_global()
        return self._global

    def update_subset_from_global(self, name: str) -> None:
        """Update ``name`` subset with values from the global configuration."""

        # Only keys present in the subset are overwritten to preserve
        # additional user defined values.
        global_cfg = self.load_global().__dict__
        subset = self.load_subset(name)
        subset.update({k: global_cfg[k] for k in subset.keys() if k in global_cfg})
        self.dump_subset(name)

    def split_all(self) -> None:
        """Refresh all known subsets from the global configuration."""

        # Each ``*.yaml`` or ``*.json`` file under the configuration directory
        # is treated as a subset and updated in place.
        for file in self.paths.cfg_dir().glob(f"*{self.serializer.ext}"):
            self.update_subset_from_global(file.stem)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def get(self, key: str) -> Any:
        """Return attribute ``key`` from the global configuration."""

        # ``load_global`` ensures the configuration is loaded only once.
        return getattr(self.load_global(), key)

    def set(self, key: str, value: Any) -> None:
        """Set ``key`` in the global configuration and persist changes."""

        # Persist the modification immediately so other components see it.
        setattr(self.load_global(), key, value)
        self.dump_global()

