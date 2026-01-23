from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional
import hashlib
import h5py

from indexer import FileMeta


class Source(ABC):
    @abstractmethod
    def open(self, meta: FileMeta) -> BinaryIO:
        raise NotImplementedError


class Sink(ABC):
    @abstractmethod
    def open(self, meta: FileMeta, name: str) -> BinaryIO:
        raise NotImplementedError


class FSSource(Source):
    def open(self, meta: FileMeta) -> BinaryIO:
        return meta.filepath.open("rb")


@dataclass
class FSSink(Sink):
    out_root: Path

    def open(self, meta: FileMeta, name: str) -> BinaryIO:
        self.out_root.mkdir(parents=True, exist_ok=True)
        return (self.out_root / name).open("wb")


@dataclass
class H5Source(Source):
    h5_path: Path
    base: str  # "/raw" or "/converted"
    dataset_name: str = "content"

    class _Reader(BinaryIO):
        def __init__(self, ds: h5py.Dataset, chunk: int):
            self._ds = ds
            self._pos = 0
            self._chunk = chunk

        def readable(self) -> bool:
            return True

        def writable(self) -> bool:
            return False

        def seekable(self) -> bool:
            return True

        def read(self, size: int = -1) -> bytes:
            n = int(self._ds.shape[0])
            if self._pos >= n:
                return b""

            if size is None or size < 0:
                size = n - self._pos

            size = min(size, n - self._pos)
            start = self._pos
            end = self._pos + size
            arr = self._ds[start:end]
            self._pos = end
            return bytes(arr)

        def seek(self, offset: int, whence: int = 0) -> int:
            n = int(self._ds.shape[0])
            if whence == 0:
                self._pos = max(0, min(n, offset))
            elif whence == 1:
                self._pos = max(0, min(n, self._pos + offset))
            elif whence == 2:
                self._pos = max(0, min(n, n + offset))
            return self._pos

        def tell(self) -> int:
            return self._pos

        def close(self) -> None:
            return None

    def _file_id(self, meta: FileMeta) -> str:
        return hashlib.sha1(meta.filepath.as_posix().encode("utf-8")).hexdigest()

    def open(self, meta: FileMeta) -> BinaryIO:
        fid = self._file_id(meta)
        with h5py.File(self.h5_path, "r") as h5:
            if self.base == "/raw":
                g = h5[f"{self.base}/{fid}"]
                ds = g[self.dataset_name]
            else:
                g = h5[f"{self.base}/{fid}/converg"]
                ds = g[self.dataset_name]

            # NOTE: we must keep file open while reader is used -> reopen in reader
        return self._open_reader(meta)

    def _open_reader(self, meta: FileMeta) -> BinaryIO:
        fid = self._file_id(meta)
        h5 = h5py.File(self.h5_path, "r")

        if self.base == "/raw":
            ds = h5[f"{self.base}/{fid}/{self.dataset_name}"]
        else:
            ds = h5[f"{self.base}/{fid}/converg/{self.dataset_name}"]

        r = self._Reader(ds, chunk=8 * 1024 * 1024)

        class _Closable(BinaryIO):
            def readable(self) -> bool: return r.readable()
            def writable(self) -> bool: return False
            def seekable(self) -> bool: return r.seekable()
            def read(self, size: int = -1) -> bytes: return r.read(size)
            def seek(self, offset: int, whence: int = 0) -> int: return r.seek(offset, whence)
            def tell(self) -> int: return r.tell()
            def close(self) -> None:
                try:
                    r.close()
                finally:
                    h5.close()

        return _Closable()


@dataclass
class H5Sink(Sink):
    h5_path: Path
    base: str  # "/raw" or "/converted"
    chunk_bytes: int = 8 * 1024 * 1024

    class _Writer(BinaryIO):
        def __init__(self, ds: h5py.Dataset):
            self._ds = ds
            self._pos = int(ds.shape[0])

        def readable(self) -> bool:
            return False

        def writable(self) -> bool:
            return True

        def seekable(self) -> bool:
            return False

        def write(self, b: bytes) -> int:
            if not b:
                return 0
            n = len(b)
            self._ds.resize((self._pos + n,))
            self._ds[self._pos:self._pos + n] = memoryview(b)
            self._pos += n
            return n

        def close(self) -> None:
            return None

    def _file_id(self, meta: FileMeta) -> str:
        return hashlib.sha1(meta.filepath.as_posix().encode("utf-8")).hexdigest()

    def _write_meta(self, g: h5py.Group, meta: FileMeta) -> None:
        g.attrs["source_path"] = meta.filepath.as_posix()
        g.attrs["filetype"] = ".".join(meta.filetype)
        g.attrs["filedate_iso"] = meta.filedate.isoformat()
        if meta.shot is None:
            if "shot" in g.attrs:
                del g.attrs["shot"]
        else:
            g.attrs["shot"] = int(meta.shot)

    def open(self, meta: FileMeta, name: str) -> BinaryIO:
        fid = self._file_id(meta)
        h5 = h5py.File(self.h5_path, "a")

        if self.base == "/raw":
            g = h5.require_group(f"{self.base}/{fid}")
            self._write_meta(g, meta)
            ds_path = f"{self.base}/{fid}/{name}"
        else:
            g = h5.require_group(f"{self.base}/{fid}/converg")
            self._write_meta(g, meta)
            ds_path = f"{self.base}/{fid}/converg/{name}"

        if ds_path in h5:
            del h5[ds_path]

        ds = h5.create_dataset(
            ds_path,
            shape=(0,),
            maxshape=(None,),
            dtype="u1",
            chunks=(max(1024, min(self.chunk_bytes, 1024 * 1024)),),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )

        w = self._Writer(ds)

        class _Closable(BinaryIO):
            def readable(self) -> bool: return False
            def writable(self) -> bool: return True
            def seekable(self) -> bool: return False
            def write(self, b: bytes) -> int: return w.write(b)
            def close(self) -> None:
                try:
                    w.close()
                finally:
                    h5.close()

        return _Closable()
