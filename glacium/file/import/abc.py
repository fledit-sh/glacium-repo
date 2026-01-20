from __future__ import annotations

from abc import ABC, abstractmethod
from .meta import FileMeta
from .result import ConvResult


class Parser(ABC):
    @abstractmethod
    def parse(self, content: bytes | str, meta: FileMeta) -> ConvResult:
        raise NotImplementedError
