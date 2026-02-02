from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterator
from pathlib import Path
from dataclasses import dataclass

# Artifact
@dataclass(frozen=True)
class FileMeta:
    fpath: Path
    ftype: tuple | None = None
    fdate: datetime | None = None
    shot: int | None = None

class Reader(ABC):
    @abstractmethod
    def read(self, meta: FileMeta) -> Iterator:
        raise NotImplementedError

class Writer(ABC):
    @abstractmethod
    def write(self, meta: FileMeta, data: Iterator) -> None:
        pass

class FileStreamReader(Reader):
    def read(self, meta: FileMeta) -> Iterator[str]:
        with meta.fpath.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                yield line

class FileStreamWriter(Writer):
    def write(self, meta: FileMeta, data: Iterator[str]) -> None:
        meta.fpath.parent.mkdir(parents=True, exist_ok=True)
        with meta.fpath.open("w", encoding="utf-8", errors="replace") as f:
            for line in data:
                f.write(line+"\n")

