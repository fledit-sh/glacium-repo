import logging

from glacium2.index import FsIndexer, TypeIndex
from pathlib import Path

class DocumentLoader:
    def __init__(self):
        self._fsindexer = FsIndexer(".")
        self._typeindex = TypeIndex()

    def load(self, filename):
        meta = self._fsindexer.acquire(Path(filename))
        if meta is None:
            raise FileNotFoundError(f"File {filename} not found")
        document_class = self._typeindex.get(meta.ftype)
        doc = document_class()
        doc.load(filename)
        return doc


