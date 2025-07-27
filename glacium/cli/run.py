"""Execute jobs for the current or all projects."""

import click
from glacium.utils.logging import log_call, log
from pathlib import Path
from glacium.utils.current import load as load_current
from glacium.managers.project_manager import ProjectManager

from .utils import runs_root

@click.command("run")
@click.argument("jobs", nargs=-1)
@click.option(
    "--all",
    "run_all",
    is_flag=True,
    help="Alle Projekte nacheinander ausführen; wiederholt fehlgeschlagene Jobs",
)
@log_call
def cli_run(jobs: tuple[str], run_all: bool):
    """Führt die Jobs des aktuellen Projekts aus.
    JOBS sind optionale Jobnamen, die ausgeführt werden sollen.
    Mit ``--all`` werden alle Projekte verarbeitet und Jobs im Status
    ``PENDING`` oder ``FAILED`` ausgeführt."""

    pm = ProjectManager(runs_root())

    if run_all:
        for uid in pm.list_uids():
            click.echo(f"[{uid}]")
            try:
                pm.load(uid).job_manager.run(jobs or None, include_failed=True)
            except FileNotFoundError:
                click.echo(f"[red]Projekt '{uid}' nicht gefunden.[/red]")
            except Exception as err:  # noqa: BLE001
                log.error(f"{uid}: {err}")
        return

    uid = load_current()
    if uid is None:
        raise click.ClickException(
            "Kein Projekt ausgewählt.\n"
            "Erst 'glacium projects' + 'glacium select <Nr>'.",
        )

    try:
        pm.load(uid).job_manager.run(jobs or None)
    except FileNotFoundError:
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.") from None

if __name__ == "__main__":
    cli_run()

