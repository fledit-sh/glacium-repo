"""Select a project UID and store it as the current project."""

import click
from rich.console import Console

from glacium.constants import RUNS_DIR
from glacium.utils.current import save
from glacium.utils.ProjectIndex import list_projects

console = Console()


@click.command("select")
@click.argument("project")  # Nummer **oder** UID
def cli_select(project: str):
    """Projekt auswählen (Nr oder UID) und merken."""
    root = RUNS_DIR
    items = list_projects(root)

    # Nummer → UID umwandeln
    if project.isdigit():
        idx = int(project) - 1
        if idx < 0 or idx >= len(items):
            raise click.ClickException("Ungültige Nummer.")
        uid = items[idx].uid
    else:
        uid = project

    if not (root / uid).exists():
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.")

    save(uid)
    console.print(f"[green]Projekt ausgewählt:[/] {uid}")
