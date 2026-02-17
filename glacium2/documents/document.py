from ..index import FsIndexer
from ..io import FileStreamReader
from ..lineparser import *

LINE_TYPES = [
    LineBlank,
    LineCategory,
    LineComment,
    LineKeyArgs,
]

class Document:
    def __init__(self):
        self.lines = []
        self._indexer = FsIndexer(".")
        self._reader = FileStreamReader()

    def open(self, fpath: str):
        with open(fpath) as f:
            for raw in f:
                for T in LINE_TYPES:
                    try:
                        self.lines.append(T(raw))
                        break
                    except ValueError:
                        pass
                else:
                    self.lines.append(LineUnknown(raw))
