from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import List

@dataclass(frozen=True)
class FileMeta:
    filepath: Path
    filetype: str
    filedate: datetime
    shot: int | None

@dataclass
class Indexer:
    root: Path
    files: List[FileMeta] = field(default_factory=list)

    def __post_init__(self):
        self.index_files()

    def index_files(self) -> None:
        files = []
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

        self.files = files