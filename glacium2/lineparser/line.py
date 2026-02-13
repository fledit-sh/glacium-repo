from dataclasses import dataclass
from typing import Tuple, Enum

class LineType:
    pass

@dataclass
class Line:
    raw: str

class LineParser:
    def __init__(self, line: Line):
        self.raw = line.raw
