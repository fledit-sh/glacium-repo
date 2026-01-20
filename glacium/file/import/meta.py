from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class FileMeta:
    filepath: Path
    filetype: str
    filedate: datetime
    shot: int | None
