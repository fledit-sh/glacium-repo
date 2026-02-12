class Writer(ABC):
    @abstractmethod
    def write(self, meta: FileMeta, data: Iterator) -> None:
        pass