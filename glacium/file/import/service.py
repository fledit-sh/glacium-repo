from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .indexer import FileMeta, TypeIndex
from .files import FSSource, FSSink, H5Source, H5Sink


@dataclass
class ConvergJobs:
    registry: TypeIndex

    def _get(self):
        conv = self.registry.get(("converg", "drop"))
        if conv is None:
            raise KeyError("No converter registered for ('converg','drop')")
        return conv

    def fs_convert_to_fs(self, meta: FileMeta, out_root: Path) -> None:
        conv = self._get()
        src = FSSource()
        sink = FSSink(out_root=out_root)
        conv.convert(meta, src, sink)

    def fs_to_h5_raw(self, meta: FileMeta, h5_path: Path) -> None:
        src = FSSource()
        sink = H5Sink(h5_path=h5_path, base="/raw")
        fin = src.open(meta)
        try:
            fout = sink.open(meta, "content")
            try:
                while True:
                    buf = fin.read(8 * 1024 * 1024)
                    if not buf:
                        break
                    fout.write(buf)
            finally:
                fout.close()
        finally:
            fin.close()

    def fs_convert_to_h5_converted(self, meta: FileMeta, h5_path: Path) -> None:
        conv = self._get()
        src = FSSource()
        sink = H5Sink(h5_path=h5_path, base="/converted")
        conv.convert(meta, src, sink)

    def h5_raw_to_h5_converted(self, meta: FileMeta, h5_path: Path) -> None:
        conv = self._get()
        src = H5Source(h5_path=h5_path, base="/raw")
        sink = H5Sink(h5_path=h5_path, base="/converted")
        conv.convert(meta, src, sink)

    def h5_raw_to_fs_spawn(self, meta: FileMeta, h5_path: Path, out_root: Path) -> None:
        src = H5Source(h5_path=h5_path, base="/raw")
        sink = FSSink(out_root=out_root)

        fin = src.open(meta)
        try:
            name = meta.filepath.name
            fout = sink.open(meta, name)
            try:
                while True:
                    buf = fin.read(8 * 1024 * 1024)
                    if not buf:
                        break
                    fout.write(buf)
            finally:
                fout.close()
        finally:
            fin.close()

    def h5_converted_to_fs_spawn(self, meta: FileMeta, h5_path: Path, out_root: Path) -> None:
        src = H5Source(h5_path=h5_path, base="/converted")
        sink = FSSink(out_root=out_root)

        fin = src.open(meta)
        try:
            name = meta.filepath.name + ".converg"
            fout = sink.open(meta, name)
            try:
                while True:
                    buf = fin.read(8 * 1024 * 1024)
                    if not buf:
                        break
                    fout.write(buf)
            finally:
                fout.close()
        finally:
            fin.close()
