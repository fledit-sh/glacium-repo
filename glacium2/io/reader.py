from abc import ABC, abstractmethod
from ..core import FileMeta
from typing import Iterator

class Reader(ABC):
    @abstractmethod
    def read(self, meta: FileMeta) -> Iterator:
        raise NotImplementedError

