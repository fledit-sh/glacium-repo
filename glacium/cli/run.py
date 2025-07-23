"""Execute jobs for the current or all projects."""

import click
from glacium.utils.logging import log_call
from pathlib import Path
from glacium.services import RunService

ROOT = Path("runs")


@click.command("run")
@click.argument("jobs", nargs=-1)
@click.option(
    "--all", "run_all", is_flag=True, help="Alle Projekte nacheinander ausführen"
)
@log_call
def cli_run(jobs: tuple[str], run_all: bool):
    """Führt die Jobs des aktuellen Projekts aus.
    JOBS sind optionale Jobnamen, die ausgeführt werden sollen.
    Mit ``--all`` werden alle Projekte verarbeitet."""

    service = RunService(ROOT)
    try:
        executed = service.run(jobs, run_all)
    except RuntimeError as err:
        raise click.ClickException(str(err)) from None

    for uid in executed:
        click.echo(f"[{uid}]")


if __name__ == "__main__":
    cli_run()
