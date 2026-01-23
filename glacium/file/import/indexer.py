from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass(frozen=True)
class FileMeta:
    filepath: Path
    filetype: tuple
    filedate: datetime
    shot: int | None


class Indexer(ABC):
    @abstractmethod
    def index(self) -> list[FileMeta]:
        raise NotImplementedError

    def __iter__(self):
        return iter(self.index())


class Converter(ABC):
    pass

class ConfigDropConverter(Converter):
    pass

class ConvergDropConverter(Converter):
    pass




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




@dataclass
class FsIndexer(Indexer):
    root: Path
    files: List[FileMeta] = field(default_factory=list)

    def __post_init__(self):
        self.files = self.index()

    def index(self) -> List[FileMeta]:
        files: List[FileMeta] = []

        for p in self.root.rglob("*"):
            if not p.is_file():
                continue

            tokens = p.name.split(".")

            shot: int | None = None
            filetype_tokens: list[str] = []

            for tok in tokens:
                if tok.isdigit() and len(tok) == 6 and shot is None:
                    shot = int(tok)
                else:
                    filetype_tokens.append(tok)

            filetype = tuple(filetype_tokens)
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

