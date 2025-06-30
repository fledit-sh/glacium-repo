from __future__ import annotations
from hydra import main
from omegaconf import DictConfig
from .cli import cli


@main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:  # pragma: no cover - thin wrapper
    cli()

if __name__ == "__main__":  # pragma: no cover
    main()
