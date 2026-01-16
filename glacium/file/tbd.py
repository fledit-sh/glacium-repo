from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Generic, TypeVar, Type, Dict

T = TypeVar("T")
OnChange = Callable[[str, Any], None]

class SimulationCase:
    """
    The simulation case defines the
    """
    pools = {
        "GUI": VarPool(),
        "GLB": VarPool(),
        "PWS": VarPool(),
    }

class VarPool:
    name: str = "Unnamed Variable Pool"
    _vars: Dict[str, ControlledVar] = field(default_factory=dict)

    def attach(self, v: ControlledVar[Any]):
        self._vars[v.key] = v

    def __getitem__(self, item):
        return self._vars[item]

    def __setitem__(self, key, value):
        self._vars[key].value = value




@dataclass
class ControlledVar(Generic[T]):
    """
    The controlled variable will be used to extend the behaviour of a certain variable
    """
    key: str
    _value: T = None

    min: Optional[T] = None
    max: Optional[T] = None

    enabled: bool = True
    hidden: bool = False

    _value_type: Type = field(init=False, repr=False)

    def __post_init__(self):
        self._value_type = type(self._value)
        self._assert_value_type(self._value)
        self._assert_boundaries(self._value)
        self.value = self._value

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        self._assert_enabled()
        self._assert_value_type(new_value)
        self._assert_boundaries(new_value)
        self._value = new_value

    def _assert_boundaries(self, v: T) -> None:
        if self.min is not None:
            if v < self.min:
                raise ValueError("Value must be greater than min")

        if self.max is not None:
            if v > self.max:
                raise ValueError("Value must be less than max")

    def _assert_enabled(self) -> None:
        if not self.enabled:
            raise ValueError(f"{self.key}: variable is disabled")

    def _assert_value_type(self, v: object) -> None:
        if not isinstance(v, self._value_type):
            raise TypeError("Wrong Value Type")

gui_pool = VarPool("GUI Pool")
gui_pool.attach(ControlledVar("FENSAP_TEMPERATURE", 273.15, 263.12, 293.15))
gui_pool.attach(ControlledVar("FENSAP_LWC", 0.547))
gui_pool.attach(ControlledVar("FENSAP_MVD", 20))
gui_pool.attach(ControlledVar("FENSAP_PRESSURE", 100000))
gui_pool.attach(ControlledVar("MSH_FILE", "grid.file"))

print(gui_pool["FENSAP_TEMPERATURE"])
gui_pool["FENSAP_TEMPERATURE"] = 265.0
print(gui_pool["MSH_FILE"])

var_pool = VarPool("Variable Pool")



