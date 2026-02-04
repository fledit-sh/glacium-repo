from __future__ import annotations
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Iterable, Iterator, Optional
from .files import FileMeta
import re

class Converter(ABC):
    """
    Streaming converter:
    - feed_line(): optional output line (None => skip)
    - finalize(): optional tail (e.g., if you buffered header info)
    - convert(): wraps a whole stream
    """

    @abstractmethod
    def feed_line(self, line: str) -> Optional[str]:
        raise NotImplementedError

    def finalize(self) -> Iterator[str]:
        # default: nothing to flush
        if False:
            yield ""  # pragma: no cover

    def convert(self, lines: Iterable[str]) -> Iterator[str]:
        for line in lines:
            out = self.feed_line(line.rstrip("\n"))
            if out is not None:
                yield out
        yield from self.finalize()


class ConvergDropConverter(Converter):
    def __init__(self) -> None:
        self.ready = False
        self.ncols: int | None = None

        self.header = [
            "time_step",
            "newton_iteration",
            "cpu_time",
            "overall_residual_drop",
            "total_beta_drop",
            "change_in_total_beta_drop",
            "alpha_residual_drop",
            "momentum_residual_drop",
            "drop_diameter_residual",
            "droplet_mass_deficit_pct",
        ]

    def check(self, cols: list[str], raw: str) -> None:
        if self.ncols is None:
            self.ncols = len(self.header)

        if len(cols) != self.ncols:
            raise ValueError(
                f"Data column mismatch: expected={self.ncols} got={len(cols)}. Line: {raw}"
            )

    def emit(self) -> str:
        self.ready = True
        return ",".join(self.header)

    def feed_line(self, line: str) -> Optional[str]:
        raw = line.strip()
        if not raw:
            return None

        if raw.startswith("#"):
            return None

        cols = raw.split()
        self.check(cols, raw)

        if not self.ready:
            return self.emit()

        return ",".join(cols)


class ConfigDropConverter(Converter):
    def feed_line(self, line: str) -> Optional[str]:
        s = line.rstrip("\n")
        return s if s.strip() else None


@dataclass
class TypeIndex:

    _index: Dict = field(default_factory=dict)

    def __post_init__(self):
        self._index = {
            ("config","drop"): ConfigDropConverter(),
            ("converg", "drop"): ConvergDropConverter()
        }

    def get(self, filetype: tuple[str, ...]) -> Converter | None:
        return self._index.get(filetype)


class Indexer(ABC):
    @abstractmethod
    def index(self) -> list[FileMeta]:
        raise NotImplementedError

    def __iter__(self):
        return iter(self.index())


@dataclass
class FsIndexer(Indexer):

    root: Path
    files: List[FileMeta] = field(default_factory=list)

    def __post_init__(self):
        self.files = self.index()

    def acquire(self, fpath: Path) -> FileMeta | None:
        if not fpath.is_file():
            return None

        tokens = fpath.name.split(".")

        shot: int | None = None
        filetype_tokens: list[str] = []

        for tok in tokens:
            if tok.isdigit() and len(tok) == 6 and shot is None:
                shot = int(tok)
            else:
                filetype_tokens.append(tok)

        return FileMeta(
            fpath=fpath,
            ftype=tuple(filetype_tokens),
            fdate=datetime.fromtimestamp(fpath.stat().st_mtime),
            shot=shot,
        )

    def index(self) -> List[FileMeta]:
        files: List[FileMeta] = []

        for p in self.root.rglob("*"):
            meta = self.acquire(p)
            if meta is not None:
                files.append(meta)

        return files


