from abc import ABC, abstractmethod
from ..core import FileMeta
from typing import Iterator

class Writer(ABC):
    @abstractmethod
    def write(self, meta: FileMeta, data: Iterator) -> None:
        pass