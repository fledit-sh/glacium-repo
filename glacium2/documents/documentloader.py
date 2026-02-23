from glacium2.index import FsIndexer, TypeIndex


class DocumentLoader:
    def __init__(self):
        self._fsindexer = FsIndexer(".")
        self._typeindex = TypeIndex()

    def load(self, filename):
        meta = self._fsindexer.acquire(filename)
        document_generator = self._typeindex.get(meta.ftype)
        return document_generator.load(filename)


