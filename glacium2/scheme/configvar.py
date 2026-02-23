from dataclasses import dataclass
from typing import Any

@dataclass
class ConfigVar:
    name: str
    category: str
    value: str
