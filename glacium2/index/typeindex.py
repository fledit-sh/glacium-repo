import logging
from dataclasses import dataclass, field
from typing import Dict
from ..documents.document import Document
from ..documents.docconfig import DocConfig

logger = logging.getLogger()

@dataclass
class TypeIndex:

    _index: Dict = field(default_factory=dict)

    def __post_init__(self):
        self._index = {
            ("config","drop"): DocConfig,
            ("converg", "drop"): DocConfig
        }

    def get(self, filetype: tuple[str, ...]) -> Document:
        logger.info(f"get: {self._index.get(filetype)}")

        return self._index.get(filetype)