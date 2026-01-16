from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Generic, TypeVar, Type


T = TypeVar("T")


@dataclass
class ControlledVar(Generic[T]):
    """
    The controlled variable will be used to extend the behaviour of a certain variable
    """
    key: str
    _value: T

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


x = ControlledVar("IMPORTANT_VAR", 4, 3, 5)
print(x)
x.value = 4
print(x.value)


from dataclasses import dataclass, field
from typing import Generic, Optional, Type, TypeVar

T = TypeVar("T")


@dataclass
class ControlledVar(Generic[T]):
    """
    Controlled variable with optional bounds and UI flags.
    Generic typing is for static type-checkers; runtime enforcement is implemented explicitly.
    """
    key: str
    value: T

    min: Optional[T] = None
    max: Optional[T] = None

    enabled: bool = True
    hidden: bool = False

    # runtime type lock (not part of the public schema)
    _value_type: Type = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._value_type = type(self.value)
        self._validate_bounds_types()
        self._validate_value_in_bounds()

    def set(self, new_value: T) -> None:
        """Set value with type + bounds validation."""
        self._ensure_enabled()
        self._ensure_type(new_value)
        self.value = new_value
        self._validate_value_in_bounds()

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise ValueError(f"{self.key}: variable is disabled")

    def _ensure_type(self, v: object) -> None:
        if not isinstance(v, self._value_type):
            raise TypeError(
                f"{self.key}: expected {self._value_type.__name__}, got {type(v).__name__}"
            )

    def _validate_bounds_types(self) -> None:
        # If bounds are set, they must match the locked value type
        if self.min is not None and not isinstance(self.min, self._value_type):
            raise TypeError(f"{self.key}: min must be {self._value_type.__name__}")
        if self.max is not None and not isinstance(self.max, self._value_type):
            raise TypeError(f"{self.key}: max must be {self._value_type.__name__}")

        # If both bounds are set, ensure ordering (only if comparable)
        if self.min is not None and self.max is not None:
            try:
                if self.min > self.max:
                    raise ValueError(f"{self.key}: min > max")
            except TypeError:
                raise TypeError(f"{self.key}: min/max not comparable for this type")

    def _validate_value_in_bounds(self) -> None:
        # Only validate if bounds exist; requires comparability
        if self.min is not None:
            try:
                if self.value < self.min:
                    raise ValueError(f"{self.key}: value < min")
            except TypeError:
                raise TypeError(f"{self.key}: value not comparable with min")

        if self.max is not None:
            try:
                if self.value > self.max:
                    raise ValueError(f"{self.key}: value > max")
            except TypeError:
                raise TypeError(f"{self.key}: value not comparable with max")
