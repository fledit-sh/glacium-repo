from dataclasses import dataclass, field
from typing import Dict

from ..converter import ConfigDropConverter, ConvergDropConverter

@dataclass
class TypeIndex:

    _index: Dict = field(default_factory=dict)

    def __post_init__(self):
        self._index = {
            ("config","drop"): ConfigDropConverter(),
            ("converg", "drop"): ConvergDropConverter()
        }

    def get(self, filetype: tuple[str, ...]) -> Converter | None:
        return self._index.get(filetype)