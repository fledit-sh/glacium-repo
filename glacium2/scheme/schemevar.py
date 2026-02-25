from dataclasses import dataclass
from typing import Any, Sequence

@dataclass(frozen=True)
class SchemaVar:
    stype: str = ""
    dtype: str = ""
    n: int | None = None
    default: Any = None
    description: str = ""
    vmin: int | float | None = None
    vmax: int | float | None = None
    quoted: bool = False
    options: Sequence[Any] | None = None