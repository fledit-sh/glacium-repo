from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class SchemaVariable:
    stype: str = ""
    dtype: str = ""
    n: int | None = None
    default: Any = None
    description: str = ""
    vmin: int | float | None = None
    vmax: int | float | None = None
    quoted: bool = False