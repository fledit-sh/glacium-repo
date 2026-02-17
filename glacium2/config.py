from dataclasses import dataclass
import yaml
from typing import Any

@dataclass
class Config:
    data: dict[str, dict[str, Any]]

    @classmethod
    def load(cls, path: str) -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            return cls(yaml.safe_load(f) or {})

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.data, f, sort_keys=False, indent=2)
