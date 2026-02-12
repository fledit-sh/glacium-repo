from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

@dataclass(frozen=True)
class FileMeta:
    fpath: Path
    ftype: tuple | None = None
    fdate: datetime | None = None
    shot: int | None = None
