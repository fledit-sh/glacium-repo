from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    import pyvista as pv
    DataSetLike = pv.DataSet | pv.MultiBlock
else:
    DataSetLike = Any


class MeshReader(Protocol):
    def read(self, path: str) -> DataSetLike:
        ...
