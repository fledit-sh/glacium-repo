from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
import hashlib
import h5py

from .indexer import FileMeta


def fileid(meta: FileMeta) -> str:
    return hashlib.sha1(meta.filepath.as_posix().encode("utf-8")).hexdigest()


def writemeta(group: h5py.Group, meta: FileMeta) -> None:
    group.attrs["source_path"] = meta.filepath.as_posix()
    group.attrs["filetype"] = ".".join(meta.filetype)
    group.attrs["filedate_iso"] = meta.filedate.isoformat()
    if meta.shot is None:
        if "shot" in group.attrs:
            del group.attrs["shot"]
    else:
        group.attrs["shot"] = int(meta.shot)


class H5Reader(BinaryIO):
    def __init__(self, h5: h5py.File, ds: h5py.Dataset, chunk: int):
        self._h5 = h5
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
        self._h5.close()


class H5Writer(BinaryIO):
    def __init__(self, h5: h5py.File, ds: h5py.Dataset):
        self._h5 = h5
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
        self._ds[self._pos : self._pos + n] = memoryview(b)
        self._pos += n
        return n

    def close(self) -> None:
        self._h5.close()


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
    chunk_bytes: int = 8 * 1024 * 1024

    def open(self, meta: FileMeta) -> BinaryIO:
        h5 = h5py.File(self.h5_path, "r")
        fid = fileid(meta)
        if self.base == "/raw":
            path = f"{self.base}/{fid}/{self.dataset_name}"
        else:
            path = f"{self.base}/{fid}/converg/{self.dataset_name}"
        ds = h5[path]
        io = H5Reader(h5, ds, chunk=self.chunk_bytes)
        return io


@dataclass
class H5Sink(Sink):
    h5_path: Path
    base: str  # "/raw" or "/converted"
    chunk_bytes: int = 8 * 1024 * 1024

    def open(self, meta: FileMeta, name: str) -> BinaryIO:
        h5 = h5py.File(self.h5_path, "a")
        fid = fileid(meta)
        if self.base == "/raw":
            group_path = f"{self.base}/{fid}"
        else:
            group_path = f"{self.base}/{fid}/converg"
        path = f"{group_path}/{name}"
        group = h5.require_group(group_path)
        writemeta(group, meta)

        if path in h5:
            del h5[path]

        ds = h5.create_dataset(
            path,
            shape=(0,),
            maxshape=(None,),
            dtype="u1",
            chunks=(max(1024, min(self.chunk_bytes, 1024 * 1024)),),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )
        io = H5Writer(h5, ds)
        return io
