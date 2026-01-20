from dataclasses import dataclass

@dataclass(frozen=True)
class VariableDef:
    key: str
    _value: T = None

    default = Any

    min: Optional[T] = None
    max: Optional[T] = None

    enabled: bool = True
    hidden: bool = False
    initialized: bool = False

