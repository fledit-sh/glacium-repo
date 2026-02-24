from __future__ import annotations

import pyvista as pv

from .meshreader import DataSetLike, MeshReader


class PyVistaReader(MeshReader):
    def read(self, path: str) -> DataSetLike:
        return pv.read(path)
