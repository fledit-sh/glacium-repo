"""Command line interface entry point for Glacium."""

import click
from pathlib import Path
from glacium.utils.logging import configure

# Einzel-Commands importieren
from .new import cli_new
from .run import cli_run   # sobald du run.py gebaut hast
from .list import cli_list
from .projects import cli_projects
from .select   import cli_select
from .job      import cli_job
from .sync import cli_sync
from .remove import cli_remove

@click.group(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.option("--log-level", default=None, help="Set log level")
@click.option("--log-file", type=click.Path(path_type=Path), help="Write logs to file")
@click.option("--multirun", is_flag=True, help="Execute parameter sweep via Hydra")
@click.pass_context
def cli(ctx: click.Context, log_level: str | None, log_file: Path | None, multirun: bool):
    """Glacium – project & job control."""
    configure(level=log_level or "INFO", file=log_file)

    if multirun:
        from glacium.main import main as hydra_main
        overrides = list(ctx.args) + ["--multirun", "hydra.run.dir=runs/${now:%Y-%m-%d_%H-%M-%S}"]
        hydra_main(overrides)
        ctx.exit()

# Befehle registrieren
cli.add_command(cli_new)
cli.add_command(cli_run)
cli.add_command(cli_list)
cli.add_command(cli_projects)
cli.add_command(cli_select)
cli.add_command(cli_job)
cli.add_command(cli_sync)
cli.add_command(cli_remove)

# entry-point für `python -m glacium.cli`
if __name__ == "__main__":
    cli()

