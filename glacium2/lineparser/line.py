

from abc import ABC, abstractmethod
from typing import Tuple, Any
import re

class Line(ABC):

    """
    The Line class is a parser. It takes a string to initialize and is able to assemble and disassemble
    filelines. Due to the variety of different Linetypes assembly and disassembly can be
    semantically divided.
    """

    pattern: str

    def __init__(self, raw: str):

        self.raw: str = raw
        self.ctx: Tuple[Any, ...] | None = None
        self.regex = re.compile(self.pattern)
        self.check()
        self.assemble()

    def check(self):
        if not self.regex.match(self.raw):
            raise ValueError(f"{self.__class__.__name__}: no match")

    @abstractmethod
    def assemble(self):
        raise NotImplementedError

    @abstractmethod
    def disassemble(self):
        raise NotImplementedError

    def __str__(self):
        return str(self.ctx)

