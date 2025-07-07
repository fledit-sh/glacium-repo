"""Single source of truth for all project paths.

The :class:`PathManager` hides ``pathlib`` arithmetic behind descriptive
methods while :class:`PathBuilder` allows fluent configuration of folder names.
Several design patterns are used:

1. **Builder** – customise directory names via :class:`PathBuilder`.
2. **Facade** – call ``pm.mesh_dir()`` instead of ``root / 'mesh'``.
3. **Null‑Object** – :class:`NullPath` avoids checks for missing paths.

Example
-------
>>> pm = PathBuilder(Path('runs/demo')).build()
>>> pm.mesh_dir().name
'mesh'
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable

__all__ = ["PathBuilder", "PathManager"]


# ────────────────────────────────────────────────────────────────────────────────
#  Null‑Object, um Missing‑Pfad sauber zu behandeln
# ────────────────────────────────────────────────────────────────────────────────
class NullPath(Path):  # type: ignore[misc]
    """Placeholder path object that ignores all filesystem operations."""

    def __new__(cls) -> "NullPath":  # noqa: D401
        """Create a neutral ``Path`` instance without touching the system."""
        return super().__new__(cls, "")

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
    """Fluent API to configure directory names before creating a manager."""

    def __init__(self, root: Path):
        """Initialise the builder.

        Parameters
        ----------
        root:
            Root directory of the project.
        """

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
        """Set the configuration directory name."""

        self._dirs["cfg"] = name
        return self

    def templates(self, name: str) -> "PathBuilder":
        """Set the template directory name."""

        self._dirs["tmpl"] = name
        return self

    def data(self, name: str) -> "PathBuilder":
        """Set the data directory name."""

        self._dirs["data"] = name
        return self

    def mesh(self, name: str) -> "PathBuilder":
        """Set the mesh directory name."""

        self._dirs["mesh"] = name
        return self

    def runs(self, name: str) -> "PathBuilder":
        """Set the runtime directory name."""

        self._dirs["runs"] = name
        return self

    # Finale -------------------------------------------------------------------
    def build(self) -> "PathManager":
        """Return a :class:`PathManager` using the configured directory names.

        Examples
        --------
        >>> pm = PathBuilder(Path('runs/demo')).mesh('meshfiles').build()
        >>> pm.mesh_dir().name
        'meshfiles'
        """

        return PathManager(self._root, **self._dirs)


# ────────────────────────────────────────────────────────────────────────────────
#  Facade
# ────────────────────────────────────────────────────────────────────────────────
class PathManager:
    """Provide well defined access points to all relevant paths.

    * **Facade** – external code calls ``pm.mesh_dir()`` rather than manually
      joining paths.
    """

    # default‑Ordnernamen (können via Builder überschrieben werden)
    def __init__(self, root: Path, *, cfg: str = "_cfg", tmpl: str = "_tmpl", data: str = "_data",
                 mesh: str = "mesh", runs: str = "runs"):
        """Create manager rooted at ``root`` with optional directory names.

        Parameters
        ----------
        root:
            Root directory for all project data.
        cfg, tmpl, data, mesh, runs:
            Custom names for the respective subdirectories.
        """

        self.root = root.resolve()
        self._map = {
            "cfg": cfg,
            "tmpl": tmpl,
            "data": data,
            "mesh": mesh,
            "runs": runs,
        }

    # Helper -------------------------------------------------------------------
    def _sub(self, key: str, *parts: Iterable[str | Path]) -> Path | NullPath:
        """Resolve a configured subdirectory and append optional parts."""
        dirname = self._map.get(key)
        if not dirname:
            return NullPath()
        p = self.root / dirname
        for part in parts:
            p /= part
        return p

    def ensure(self) -> None:
        """Create all base directories if they do not exist."""
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
        """Return a subdirectory in ``runs`` for a given solver."""
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
        """Path to a rendered template relative to ``tmpl`` directory."""
        return self.tmpl_dir() / Path(rel_path)

