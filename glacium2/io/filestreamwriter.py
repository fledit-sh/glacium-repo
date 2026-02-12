from .writer import Writer

class FileStreamWriter(Writer):
    def write(self, meta: FileMeta, data: Iterator[str]) -> None:
        meta.fpath.parent.mkdir(parents=True, exist_ok=True)
        with meta.fpath.open("w", encoding="utf-8", errors="replace") as f:
            for line in data:
                f.write(line+"\n")
