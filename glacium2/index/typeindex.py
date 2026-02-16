from dataclasses import dataclass, field
from typing import Dict

@dataclass
class TypeIndex:

    _index: Dict = field(default_factory=dict)

    def __post_init__(self):
        self._index = {
            ("config","drop"): 4,
            ("converg", "drop"): 4
        }

    def get(self, filetype: tuple[str, ...]) -> int | None:
        return self._index.get(filetype)