"""Configuration helpers based on Hydra."""
from __future__ import annotations
from typing import Iterable, Any
from hydra import compose, initialize_config_module
from omegaconf import OmegaConf

__all__ = ["compose_config"]


def compose_config(overrides: Iterable[str] | None = None) -> dict[str, Any]:
    """Compose configuration using ``glacium.conf`` package."""
    overrides = list(overrides) if overrides else []
    with initialize_config_module(config_module="glacium.conf", version_base=None):
        cfg = compose(config_name="config", overrides=overrides)
    return OmegaConf.to_container(cfg, resolve=True)  # type: ignore[return-value]
