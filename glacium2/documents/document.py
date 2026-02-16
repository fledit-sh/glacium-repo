from ..index import FsIndexer
from ..io import FileStreamReader
from ..lineparser import *

LINE_TYPES = [
    LineBlank,
    LineCategory,
    LineComment,
    LineKeyArgs,
    LineUnknown,
]

class Document:
    def __init__(self):
        self.lines = []
        self._indexer = FsIndexer(".")
        self._reader = FileStreamReader()

    def open(self, fpath: str):

        with open(fpath) as f:
            for line in f:
                for T in LINE_TYPES:
                    try:
                        parsed = T(line)
                        self.lines.append(parsed)
                        continue
                    except ValueError:
                        pass
                    # self.lines.append(LineUnknown(line))