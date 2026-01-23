from __future__ import annotations

from pathlib import Path
import shutil

from indexer import FsIndexer, TypeIndex
from service import ConvergJobs

from source import FSSink
from parsers import ConvergParser  # in deinem package: from .parsers import ConvergParser


# --- minimaler Converter (wie oben) ---
import io
from dataclasses import dataclass


@dataclass(frozen=True)
class ConvergDropConverter:
    parser: ConvergParser = ConvergParser()

    def convert(self, meta, src, sink) -> None:
        fin = src.open(meta)
        try:
            content = fin.read()
        finally:
            fin.close()

        res = self.parser.parse(content, meta)
        df = res.payload

        s = io.StringIO()
        df.to_csv(s, index=False)
        data = s.getvalue().encode("utf-8")

        fout = sink.open(meta, "content")
        try:
            fout.write(data)
        finally:
            fout.close()


def main() -> None:
    legacy_root = Path(".")
    out_root = Path("out_spawn")
    h5_path = Path("case.h5")

    out_root.mkdir(parents=True, exist_ok=True)
    if h5_path.exists():
        h5_path.unlink()

    # 1) Index bauen und ein converg.drop meta auswählen
    idx = FsIndexer(root=legacy_root)
    meta = next(m for m in idx.files if m.filetype == ("converg", "drop"))

    # 2) Registry bauen und unseren Converter setzen
    reg = TypeIndex()
    reg._index[("converg", "drop")] = ConvergDropConverter()

    jobs = ConvergJobs(registry=reg)

    # 3) FS -> H5 raw
    jobs.fs_to_h5_raw(meta, h5_path=h5_path)

    # 4) FS -> H5 converted (über Converter)
    jobs.fs_convert_to_h5_converted(meta, h5_path=h5_path)

    # 5) H5 raw -> FS spawn (Kontrolle)
    jobs.h5_raw_to_fs_spawn(meta, h5_path=h5_path, out_root=out_root)

    # 6) H5 converted -> FS spawn (Kontrolle)
    jobs.h5_converted_to_fs_spawn(meta, h5_path=h5_path, out_root=out_root)

    print("OK")
    print("raw   ->", out_root / meta.filepath.name)
    print("conv  ->", out_root / (meta.filepath.name + ".converg"))


if __name__ == "__main__":
    main()
