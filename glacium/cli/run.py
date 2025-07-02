"""Execute jobs for the current or all projects."""

import click

from glacium.constants import RUNS_DIR
from glacium.managers.ProjectManager import ProjectManager
from glacium.utils.current import load as load_current

ROOT = RUNS_DIR


@click.command("run")
@click.argument("jobs", nargs=-1)
@click.option(
    "--all", "run_all", is_flag=True, help="Alle Projekte nacheinander ausführen"
)
def cli_run(jobs: tuple[str], run_all: bool):
    """Führt die Jobs des aktuellen Projekts aus.
    JOBS sind optionale Jobnamen, die ausgeführt werden sollen.
    Mit ``--all`` werden alle Projekte verarbeitet."""

    pm = ProjectManager(ROOT)

    if run_all:
        for uid in pm.list_uids():
            click.echo(f"[{uid}]")
            try:
                pm.load(uid).job_manager.run(jobs or None)
            except FileNotFoundError:
                click.echo(f"[red]Projekt '{uid}' nicht gefunden.[/red]")
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
