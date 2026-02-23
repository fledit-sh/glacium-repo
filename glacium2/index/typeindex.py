from dataclasses import dataclass, field
from typing import Dict
from ..documents import Document, DocConfig

@dataclass
class TypeIndex:

    _index: Dict = field(default_factory=dict)

    def __post_init__(self):
        self._index = {
            ("config","drop"): DocConfig,
            ("converg", "drop"): DocConfig
        }

    def get(self, filetype: tuple[str, ...]) -> Document:
        return self._index.get(filetype)