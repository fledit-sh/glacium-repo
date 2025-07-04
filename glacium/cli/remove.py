"""Remove projects from the ``runs`` directory."""

import shutil
from pathlib import Path

import click
from glacium.utils.logging import log_call
from rich.console import Console

from glacium.utils.ProjectIndex import list_projects
from glacium.utils.current import load as load_current

ROOT = Path("runs")
console = Console()


@click.command("remove")
@click.argument("project", required=False)
@click.option("--all", "remove_all", is_flag=True, help="Alle Projekte löschen")
@log_call
def cli_remove(project: str | None, remove_all: bool):
    """Entfernt ein Projekt samt aller Daten.

    Ohne Argument wird das aktuell gewählte Projekt verwendet.
    Mit ``--all`` werden alle Projekte unter ./runs entfernt.
    Die Nummer entspricht der Ausgabe von ``glacium projects``.
    """

    if remove_all:
        uids = [p.name for p in ROOT.iterdir() if p.is_dir()]
    else:
        if project is None:
            uid = load_current()
            if uid is None:
                raise click.ClickException(
                    "Kein Projekt angegeben und kein Projekt ausgewählt.\n"
                    "Erst 'glacium projects' + 'glacium select <Nr>'."
                )
        else:
            if project.isdigit():
                items = list_projects(ROOT)
                idx = int(project) - 1
                if idx < 0 or idx >= len(items):
                    raise click.ClickException("Ungültige Nummer.")
                uid = items[idx].uid
            else:
                uid = project
        uids = [uid]

    for uid in uids:
        path = ROOT / uid
        if path.exists():
            shutil.rmtree(path)
            console.print(f"[green]{uid} entfernt.[/]")
        else:
            console.print(f"[red]{uid} nicht gefunden.[/]")

