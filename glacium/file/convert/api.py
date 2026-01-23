from abc import ABC, abstractmethod
from dataclasses import dataclass

class ConversionResult(ABC):
    pass

@dataclass
class Artifact:
    type: str
    name: str
    def
    pass


class Converter(ABC):
    @abstractmethod
    def convert(self, data) -> ConversionResult:
        raise NotImplementedError

class ConvergenceDropConverter(Converter):
    def convert(self, data) -> ConversionResult:



        return ConversionResult()