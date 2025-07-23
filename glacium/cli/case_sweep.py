"""Create multiple projects from parameter sweeps."""

from __future__ import annotations

from pathlib import Path
import click

from glacium.services import CaseSweepService
from glacium.utils.logging import log_call

DEFAULT_RECIPE = "multishot"


@click.command("case-sweep")
@click.option(
    "--param",
    "params",
    multiple=True,
    required=True,
    help="KEY=val1,val2,... pairs to sweep",
)
@click.option(
    "-r",
    "--recipe",
    default=DEFAULT_RECIPE,
    show_default=True,
    help="Recipe name or names joined with '+'",
)
@click.option(
    "-o",
    "--output",
    default="runs",
    show_default=True,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path, writable=True),
    help="Root directory for projects",
)
@click.option(
    "--multishots",
    type=int,
    help="Number of MULTISHOT runs",
)
@log_call
def cli_case_sweep(
    params: tuple[str], recipe: str, output: Path, multishots: int | None
) -> None:
    """Create projects for all parameter combinations."""

    service = CaseSweepService(output)
    uids = service.create_projects(params, recipe, multishots=multishots)
    for uid in uids:
        click.echo(uid)


__all__ = ["cli_case_sweep"]
