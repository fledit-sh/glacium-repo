from abc import ABC, abstractmethod
from ..core import FileMeta


class Indexer(ABC):
    @abstractmethod
    def index(self) -> list[FileMeta]:
        raise NotImplementedError

    def __iter__(self):
        return iter(self.index())