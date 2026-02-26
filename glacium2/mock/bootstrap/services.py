from __future__ import annotations

from dataclasses import dataclass

from ..services import Logger, ProjectStore, Settings


@dataclass(frozen=True)
class Services:
    logger: Logger
    settings: Settings
    project_store: ProjectStore


def make() -> Services:
    return Services(
        logger=Logger(),
        settings=Settings(),
        project_store=ProjectStore(),
    )
