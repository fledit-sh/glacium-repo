from __future__ import annotations

from typing import Callable, Dict, Type, List, Any

from glacium.utils.logging import log

class EngineFactory:
    """Registry and factory for available engine classes."""

    _engines: Dict[str, Type[Any]] = {}

    @classmethod
    def register(
        cls, engine_cls: Type[Any] | None = None, *, name: str | None = None
    ) -> Callable[[Type[Any]], Type[Any]]:
        """Class decorator to register an engine class."""

        def decorator(target: Type[Any]) -> Type[Any]:
            key = name or target.__name__
            if key in cls._engines:
                log.warning(f"Engine '{key}' wird überschrieben.")
            cls._engines[key] = target
            return target

        if engine_cls is None:
            return decorator
        return decorator(engine_cls)

    @classmethod
    def create(cls, name: str, *args, **kwargs) -> Any:
        """Instantiate the registered engine ``name`` with given arguments."""

        if name not in cls._engines:
            raise KeyError(f"Engine '{name}' nicht registriert.")
        return cls._engines[name](*args, **kwargs)

    @classmethod
    def list(cls) -> List[str]:
        """Return the list of registered engine names."""

        return sorted(cls._engines)
