from dataclasses import dataclass, field
import yaml
from typing import Any, List
from .configvar import ConfigVar

class Config:
    """
    - config holds the variables
    - a rule can be access or hook to a specific variable
    - a rule
    """

    def __init__(self, data: dict[str, dict[str, Any]]) -> None:
        self.variables = dict()
        self.convert(data)

    def convert(self, cfg: dict[str, dict[str, Any]]):
        for category, value in cfg.items():
            for k, v in value.items():
                cfg[category][k] = ConfigVar(v)
        self.variables = cfg

    def __getitem__(self, item) -> dict[str, ConfigVar]:
        return self.variables[item]
