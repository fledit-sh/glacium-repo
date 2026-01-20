from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .meta import FileMeta


class Indexer(ABC):
    @abstractmethod
    def index(self) -> list[FileMeta]:
        raise NotImplementedError

    def __iter__(self):
        return iter(self.index())


@dataclass
class FsIndexer(Indexer):
    root: Path
    files: list[FileMeta] = field(default_factory=list)

    def __post_init__(self):
        self.files = self.index()

    def index(self) -> list[FileMeta]:
        files: list[FileMeta] = []
        for p in self.root.rglob("*"):
            if p.is_file():
                tokens = p.name.split(".")

                shot = None
                if tokens[-1].isdigit():
                    shot = int(tokens.pop(-1))

                filetype = ".".join(tokens)
                filedate = datetime.fromtimestamp(p.stat().st_mtime)

                files.append(
                    FileMeta(
                        filepath=p,
                        filetype=filetype,
                        filedate=filedate,
                        shot=shot,
                    )
                )

        return files
