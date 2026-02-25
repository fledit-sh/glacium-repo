from dataclasses import dataclass
from typing import Any

@dataclass
class ConfigVar:
    value: Any | None = None

