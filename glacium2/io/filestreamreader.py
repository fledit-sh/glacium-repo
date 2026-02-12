from .reader import Reader
from ..core import FileMeta
from typing import Iterator

class FileStreamReader(Reader):
    def read(self, meta: FileMeta) -> Iterator[str]:
        with meta.fpath.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                yield line