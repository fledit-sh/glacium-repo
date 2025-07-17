from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List, Type
import json

import yaml
import matplotlib.pyplot as plt
import numpy as np

from .artifact import Artifact, ArtifactIndex, ArtifactSet

__all__ = ["PostProcessor", "write_manifest", "index_from_dict"]


def index_from_dict(data: dict[str, Any]) -> ArtifactIndex:
    """Recreate an :class:`ArtifactIndex` from a JSON-compatible dict."""
    index = ArtifactIndex()
    for run_id, artifacts in data.items():
        aset = ArtifactSet(run_id)
        for art in artifacts:
            aset.add(
                Artifact(
                    Path(art["path"]),
                    art["kind"],
                    dict(art.get("meta", {})),
                )
            )
        index[run_id] = aset
    return index


def write_manifest(index: ArtifactIndex, dest: str | Path) -> Path:
    """Write ``index`` to ``dest`` in JSON format."""
    dest = Path(dest)
    data = {
        rid: [a.to_dict() for a in aset.artifacts]
        for rid, aset in index.items()
    }
    dest.write_text(json.dumps(data, indent=2))
    return dest


class PostProcessor:
    """Lightweight access to post-processing artifacts."""

    _registry: List[Type] = []

    # ------------------------------------------------------------------
    def __init__(self, source: str | Path, *, importers: Iterable[Type] | None = None, recursive: bool = True) -> None:
        self.source = Path(source)
        self.recursive = recursive
        self.importers: List[Any] = [imp() for imp in (importers or self._registry)]
        manifest = self.source / "manifest.json"
        if manifest.exists():
            data = json.loads(manifest.read_text())
            self._index = index_from_dict(data)
        else:
            self._index = ArtifactIndex()
            self._scan()

    # ------------------------------------------------------------------
    def _scan(self) -> None:
        if not self.importers:
            return
        dirs: Iterable[Path]
        if self.recursive:
            dirs = (p for p in self.source.rglob("*") if p.is_dir())
        else:
            dirs = (p for p in self.source.iterdir() if p.is_dir())
        for d in dirs:
            for imp in self.importers:
                try:
                    detector = getattr(imp, "detect")
                    parser = getattr(imp, "parse")
                except AttributeError:
                    continue
                try:
                    if detector(d):
                        aset = parser(d)
                        self._index[aset.run_id] = aset
                        break
                except Exception:
                    continue

    # ------------------------------------------------------------------
    def map(self, pattern: str = "*.dat") -> List[Path]:
        paths: List[Path]
        if self.recursive:
            paths = sorted(self.source.rglob(pattern))
        else:
            paths = sorted(self.source.glob(pattern))
        return paths

    # ------------------------------------------------------------------
    @property
    def index(self) -> ArtifactIndex:  # pragma: no cover - trivial
        return self._index

    # ------------------------------------------------------------------
    def get(self, run_or_id: str | ArtifactSet) -> ArtifactSet:
        if isinstance(run_or_id, ArtifactSet):
            return run_or_id
        if isinstance(run_or_id, Path):
            run_or_id = run_or_id.name
        return self._index[run_or_id]

    # ------------------------------------------------------------------
    def plot(self, var: str, run_or_id: str | ArtifactSet):
        aset = self.get(run_or_id)
        art = aset.get_first(var)
        if art is None:
            raise KeyError(f"{var} not found in run {aset.run_id}")
        data = np.loadtxt(art.path)
        plt.plot(data)
        plt.xlabel("index")
        plt.ylabel(var)
        return plt.gca()

    # ------------------------------------------------------------------
    def export(self, dest: str | Path, format: str = "zip") -> Path:
        dest = Path(dest)
        if format == "zip":
            import zipfile

            with zipfile.ZipFile(dest, "w") as zf:
                for aset in self._index.values():
                    for art in aset.artifacts:
                        zf.write(art.path, arcname=f"{aset.run_id}/{art.path.name}")
        else:
            raise ValueError(f"unknown format: {format}")
        return dest

    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for run_id, aset in self._index.items():
            out[run_id] = [a.to_dict() for a in aset.artifacts]
        return out

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), sort_keys=False)

    # ------------------------------------------------------------------
    @classmethod
    def register_importer(cls, importer: Type) -> Type:
        if importer not in cls._registry:
            cls._registry.append(importer)
        return importer
