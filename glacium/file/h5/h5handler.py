from __future__ import annotations

import h5py
import logging
from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path

import numpy as np


class H5Interface(ABC):
    @abstractmethod
    def group(self, key: str) -> "H5Interface": ...

    @abstractmethod
    def attr(self, key: str, value: Any) -> "H5Interface": ...

    @abstractmethod
    def feed(self, key: str, *, path: str | Path) -> "H5Interface": ...


class H5Node(H5Interface):
    def __init__(self, g: h5py.Group):
        self._g = g

    def group(self, key: str) -> "H5Node":
        return H5Node(self._g.require_group(key))

    def attr(self, key: str, value: Any) -> "H5Node":
        self._g.attrs[key] = value
        return self

    def feed(self, key: str, *, path: str | Path) -> "H5Node":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(p)
        if not p.is_file():
            raise IsADirectoryError(p)

        data = np.fromfile(p, dtype=np.uint8)
        ds = self._g.require_dataset(key, shape=data.shape, dtype=np.uint8, exact=False)
        ds[...] = data
        ds.attrs["source_name"] = p.name
        ds.attrs["source_path"] = str(p)
        ds.attrs["source_size"] = int(p.stat().st_size)
        return self


class H5(H5Node):
    def __init__(self, name: str, mode: str = "w"):
        self.name = name
        self.mode = mode
        self.file: h5py.File | None = None
        self._log = logging.getLogger("H5")
        self._g = None  # set on enter

    def __enter__(self) -> "H5":
        self._log.info("enter %s", self.name)
        self.file = h5py.File(self.name, self.mode)
        self._g = self.file  # root group "/"
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._log.info("exit %s", self.name)
        try:
            if self.file is not None:
                self.file.close()
        finally:
            self.file = None
            self._g = None
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # liegt in der gleichen Directory wie dieses Script:
    cfg = Path(__file__).with_name("config.drop.000001")

    with H5("test.h5") as h5:
        h5.group("case") \
          .group("drop") \
          .attr("kind", "Drop3D") \
          .attr("id", 1) \
          .feed("config", path=cfg)

        h5.attr("created_by", "Noel")
