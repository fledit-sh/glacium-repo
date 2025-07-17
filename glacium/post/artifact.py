from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List

__all__ = [
    "Artifact",
    "ArtifactSet",
    "ArtifactIndex",
]


@dataclass
class Artifact:
    """Single post-processing artifact on disk."""

    path: Path
    kind: str
    meta: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    def open(self, mode: str = "rb"):
        """Open ``path`` with the given mode (default: binary read)."""
        return self.path.open(mode)

    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation of this artifact."""
        return {"path": str(self.path), "kind": self.kind, "meta": dict(self.meta)}


@dataclass
class ArtifactSet:
    """Collection of :class:`Artifact` objects belonging to one run."""

    run_id: str
    artifacts: List[Artifact] = field(default_factory=list)

    # ------------------------------------------------------------------
    def add(self, artifact: Artifact) -> None:
        self.artifacts.append(artifact)

    # ------------------------------------------------------------------
    def filter(self, *, kind: str | None = None, **meta: Any) -> "ArtifactSet":
        """Return a new :class:`ArtifactSet` filtered by ``kind`` and ``meta``."""

        items = self.artifacts
        if kind is not None:
            items = [a for a in items if a.kind == kind]
        for key, val in meta.items():
            items = [a for a in items if a.meta.get(key) == val]
        return ArtifactSet(self.run_id, list(items))

    # ------------------------------------------------------------------
    def get_first(self, kind: str) -> Artifact | None:
        """Return the first artifact matching ``kind`` if present."""

        for art in self.artifacts:
            if art.kind == kind:
                return art
        return None

    # ------------------------------------------------------------------
    def to_dataframe(self):  # pragma: no cover - optional dependency
        """Return the artifacts as a ``pandas.DataFrame``."""

        try:
            import pandas as pd
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("pandas required for to_dataframe") from exc
        return pd.DataFrame([a.to_dict() for a in self.artifacts])


@dataclass
class ArtifactIndex:
    """Mapping of run identifiers to :class:`ArtifactSet` objects."""

    runs: Dict[str, ArtifactSet] = field(default_factory=dict)

    # ------------------------------------------------------------------
    def __iter__(self) -> Iterator[str]:  # pragma: no cover - trivial
        return iter(self.runs)

    # ------------------------------------------------------------------
    def __getitem__(self, key: str) -> ArtifactSet:  # pragma: no cover - trivial
        return self.runs[key]

    # ------------------------------------------------------------------
    def __setitem__(self, key: str, value: ArtifactSet) -> None:  # pragma: no cover - trivial
        self.runs[key] = value

    # ------------------------------------------------------------------
    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.runs)

    # ------------------------------------------------------------------
    def values(self) -> Iterable[ArtifactSet]:  # pragma: no cover - trivial
        return self.runs.values()

    # ------------------------------------------------------------------
    def items(self):  # pragma: no cover - trivial
        return self.runs.items()
