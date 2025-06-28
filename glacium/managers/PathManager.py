"""glacium.managers.path_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ein *Single‑Source‑of‑Truth*‑Objekt für alle Projektpfade.

**Design‑Patterns (Refactoring‑Guru‑Stil)**
==========================================
1. **Builder** – `PathBuilder` erlaubt fluentes Konfigurieren der Ordnernamen
   (vor allem für Tests & Custom‑Layouts).
2. **Facade** – `PathManager` versteckt sämtliche `Path`‑Arithmetik hinter
   aussagekräftigen Methoden (`mesh_dir()`, `solver_file()`, …).
3. **Null‑Object** – `NullPath` verhindert `None`‑Prüfungen, wenn ein Pfad
   (noch) nicht existiert.
4. **Singleton (Borg)** – Mehrere Instanzen teilen denselben
   *state*-Dict (`_SharedState`), sodass innerhalb eines Prozesses stets die
   gleiche Struktur genutzt wird, egal wer `PathManager(root)` aufruft.

Damit bleiben alle übrigen Manager/Engines völlig frei von hartgecodeten
`Path`‑Manipulationen.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable

__all__ = ["PathBuilder", "PathManager"]


# ────────────────────────────────────────────────────────────────────────────────
#  Null‑Object, um Missing‑Pfad sauber zu behandeln
# ────────────────────────────────────────────────────────────────────────────────
class NullPath(Path):  # type: ignore[misc]
    """Ein *Path*-Platzhalter, der jede Operation überlebt."""

    _flavour = type(Path())._flavour  # intern nötig

    def __truediv__(self, key: str | Path) -> "NullPath":  # noqa: D401
        return self  # Chain bleibt Null

    def exists(self) -> bool:  # noqa: D401
        return False

    def mkdir(self, *args, **kwargs):  # noqa: D401
        # Schweigend ignorieren
        return None

    def __str__(self):  # noqa: D401
        return "<null>"


# ────────────────────────────────────────────────────────────────────────────────
#  Builder
# ────────────────────────────────────────────────────────────────────────────────
class PathBuilder:
    """Fluente API, um individuelle Ordnernamen festzulegen."""

    def __init__(self, root: Path):
        """Initialise builder with project ``root`` directory."""

        self._root = root.resolve()
        # Defaults
        self._dirs: Dict[str, str] = {
            "cfg": "_cfg",
            "tmpl": "_tmpl",
            "data": "_data",
            "mesh": "mesh",
            "runs": "runs",  # weitere Runtime‑Artefakte (FENSAP etc.)
        }

    # Builder‑Setters ----------------------------------------------------------
    def cfg(self, name: str) -> "PathBuilder":
        self._dirs["cfg"] = name
        return self

    def templates(self, name: str) -> "PathBuilder":
        self._dirs["tmpl"] = name
        return self

    def data(self, name: str) -> "PathBuilder":
        self._dirs["data"] = name
        return self

    def mesh(self, name: str) -> "PathBuilder":
        self._dirs["mesh"] = name
        return self

    def runs(self, name: str) -> "PathBuilder":
        self._dirs["runs"] = name
        return self

    # Finale -------------------------------------------------------------------
    def build(self) -> "PathManager":
        """Return a :class:`PathManager` using the configured directory names."""

        return PathManager(self._root, **self._dirs)


# ────────────────────────────────────────────────────────────────────────────────
#  Facade + Borg‑Singleton
# ────────────────────────────────────────────────────────────────────────────────
class _SharedState:  # noqa: D401  # pylance: disable=too-few-public-methods
    __shared_state: Dict[str, object] = {}

    def __init__(self):
        self.__dict__ = self.__shared_state


class PathManager(_SharedState):
    """Bietet wohldefinierte Zugriffspunkte auf alle wichtigen Ordner + Dateien.

    * **Facade:** Außenwelt ruft `pm.mesh_dir()` statt `root / "mesh"`.
    * **Borg‑Singleton:** Mehrfachinstanzen teilen State → 1 Quelle der Wahrheit.
    """

    # default‑Ordnernamen (können via Builder überschrieben werden)
    def __init__(self, root: Path, *, cfg: str = "_cfg", tmpl: str = "_tmpl", data: str = "_data",
                 mesh: str = "mesh", runs: str = "runs"):
        """Create manager rooted at ``root`` with optional directory names."""

        super().__init__()
        if not getattr(self, "_initialized", False):  # nur beim ersten Mal setzen
            self.root = root.resolve()
            self._map = {
                "cfg": cfg,
                "tmpl": tmpl,
                "data": data,
                "mesh": mesh,
                "runs": runs,
            }
            self._initialized = True

    # Helper -------------------------------------------------------------------
    def _sub(self, key: str, *parts: Iterable[str | Path]) -> Path | NullPath:
        """Internal helper resolving a sub-path or returning :class:`NullPath`."""
        dirname = self._map.get(key)
        if not dirname:
            return NullPath()
        p = self.root / dirname
        for part in parts:
            p /= part
        return p

    def ensure(self) -> None:
        """Erzeugt alle Basis‑Ordner, falls nicht vorhanden."""
        for name in self._map.values():
            (self.root / name).mkdir(parents=True, exist_ok=True)

    # Public Facade API ---------------------------------------------------------
    def cfg_dir(self) -> Path:
        """Return the configuration directory."""

        return self._sub("cfg")  # type: ignore[return-value]

    def tmpl_dir(self) -> Path:
        """Return the directory containing rendered templates."""

        return self._sub("tmpl")  # type: ignore[return-value]

    def data_dir(self) -> Path:
        """Return the directory holding project data files."""

        return self._sub("data")  # type: ignore[return-value]

    def mesh_dir(self) -> Path:
        """Return the mesh directory."""

        return self._sub("mesh")  # type: ignore[return-value]

    def runs_dir(self) -> Path:
        """Return the runtime directory for solver output."""

        return self._sub("runs")  # type: ignore[return-value]

    def solver_dir(self, solver: str) -> Path:
        """Return or create a directory for ``solver`` under the project root."""

        path = self.root / solver  # statt runs/solver
        path.mkdir(parents=True, exist_ok=True)
        return path

    # Beispiel‑Convenience ------------------------------------------------------
    def solver_subdir(self, solver: str) -> Path:
        """Unterordner in *runs* für einen Solver (z. B. *fensap*, *drop3d*)."""
        path = self.runs_dir() / solver
        path.mkdir(parents=True, exist_ok=True)
        return path

    # Dateipfade ---------------------------------------------------------------
    def global_cfg_file(self) -> Path:
        return self.cfg_dir() / "global_config.yaml"

    def job_file(self) -> Path:
        return self.cfg_dir() / "jobs.yaml"

    # Jinja‑Outputs ------------------------------------------------------------
    def rendered_template(self, rel_path: str | Path) -> Path:
        """Pfad zu einem einmal gerenderten Template."""
        return self.tmpl_dir() / Path(rel_path)

