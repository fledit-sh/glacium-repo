from files import FileMeta, FileStreamReader, FileStreamWriter
from indexer import TypeIndex, FsIndexer
from pathlib import Path

# initialising filemet list
test_index = FsIndexer(Path("import")) # should be str
print(test_index)

# create the type index
type_index = TypeIndex()

# get converters based on file list and convert the file (here append)
converters = []
for file in test_index.index():
    mygen = type_index.get(file.ftype)
    if mygen:
        converters.append(file.ftype)

class Orchestrator:
    def draw(self):
        pass

class TestOrchestration:

    def __init__(self) -> None:

        self._types = TypeIndex()
        self._reader = FileStreamReader()
        self._writer = FileStreamWriter()

    def convert(self, fpath: Path, target: Path) -> None:
        idx = FsIndexer(root=fpath.parent)
        meta = idx.acquire(fpath)
        if meta is None or meta.ftype is None:
            return

        conv = self._types.get(meta.ftype)
        if conv is None:
            return

        lines = self._reader.read(meta)
        out_lines = conv.convert(lines)

        out_meta = FileMeta(
            fpath=target,
            ftype=tuple([*meta.ftype, "converted"]),
            fdate=meta.fdate,
            shot=meta.shot,
        )
        self._writer.write(out_meta, out_lines)

TestOrchestration().convert(
    fpath=Path("import/converg.drop.000001"),
    target=Path("converg.drop.000001.converted"),
)

# delete raw files and pack them in h5
# put converted and raw in same h5 file?
# create lightweight converted h5 file?
# raw data should be preserved
# glacium.scan(".")
# glacium.convert(filename="converg.drop.00001", target="converg.drop.00001.converted")
# glacium.convert()
# glacium.project("")
print(converters)
