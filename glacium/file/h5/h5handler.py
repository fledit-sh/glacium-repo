from glacium.file.files import FileStreamReader
from glacium.file.indexer import FsIndexer
from pathlib import Path

indexer = FsIndexer(Path("."))
reader = FileStreamReader()
meta = indexer.acquire(Path("config.drop.000001"))
for line in reader.read(meta):
    print(line)