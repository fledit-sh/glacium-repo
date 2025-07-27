"""Command line interface entry point for Glacium."""

from pathlib import Path

import click

# Einzel-Commands importieren
from .new import cli_new
from .init import cli_init
from .run import cli_run   # sobald du run.py gebaut hast
from .list import cli_list
from .projects import cli_projects
from .select   import cli_select
from .job import cli_job
from .sync import cli_sync
from .remove import cli_remove
from .generate import cli_generate
from .update import cli_update
from .info import cli_info
from .case_sweep import cli_case_sweep

@click.group()
@click.option(
    "--dir",
    "runs_dir",
    default="runs",
    show_default=True,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Directory containing projects",
)
@click.pass_context
def cli(ctx: click.Context, runs_dir: Path) -> None:
    """Glacium – project & job control."""

    ctx.obj = runs_dir

# Befehle registrieren
cli.add_command(cli_new)
cli.add_command(cli_init)
cli.add_command(cli_run)
cli.add_command(cli_list)
cli.add_command(cli_projects)
cli.add_command(cli_select)
cli.add_command(cli_job)
cli.add_command(cli_sync)
cli.add_command(cli_remove)
cli.add_command(cli_generate)
cli.add_command(cli_update)
cli.add_command(cli_info)
cli.add_command(cli_case_sweep)

# entry-point für `python -m glacium.cli`
if __name__ == "__main__":
    cli()

