"""Job management commands grouped under ``glacium job``."""

from __future__ import annotations

from pathlib import Path

import click
from glacium.utils.logging import log_call
from rich.console import Console

ROOT = Path("runs")
console = Console()


@click.group("job", invoke_without_command=True)
@click.option(
    "--list",
    "list_all",
    is_flag=True,
    help="Alle implementierten Jobs auflisten",
)
@click.pass_context
@log_call
def cli_job(ctx: click.Context, list_all: bool) -> None:
    """Job-Utilities für das aktuell gewählte Projekt."""

    if ctx.invoked_subcommand is None:
        if list_all:
            from glacium.utils import list_jobs

            for idx, name in enumerate(list_jobs(), start=1):
                click.echo(f"{idx:2d}) {name}")
        else:
            click.echo(ctx.get_help())


# Subcommand implementations -------------------------------------------------
from . import reset  # noqa: E402,F401
from . import list as list_command  # noqa: E402,F401
from . import add  # noqa: E402,F401
from . import remove  # noqa: E402,F401
from . import run  # noqa: E402,F401
from . import select  # noqa: E402,F401

__all__ = ["cli_job"]
