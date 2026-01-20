from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .meta import FileMeta


class Parser(ABC):
    @abstractmethod
    def parse(self, content: bytes | str, meta: FileMeta) -> Any:
        raise NotImplementedError
