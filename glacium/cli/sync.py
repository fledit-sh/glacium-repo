"""Synchronise projects with the latest recipe definitions."""

import click, yaml
from glacium.utils.logging import log_call
from pathlib import Path
from glacium.managers.project_manager import ProjectManager
from glacium.utils.current import load as load_current
from glacium.utils.ProjectIndex import list_projects

ROOT = Path("runs")

@click.command("sync")
@click.argument("uid", required=False)
@click.option("--all", "sync_all", is_flag=True,
              help="Alle Projekte mit dem aktuellen Rezept abgleichen")
@log_call
def cli_sync(uid: str | None, sync_all: bool):
    """
    Synchronisiert die Job-Liste eines Projekts mit dem neuesten Rezept.
    • Ohne Argument  → aktuelles Projekt (.glacium_current)
    • Mit UID       → nur dieses Projekt
    • --all         → alle Projekte unter ./runs
    """
    pm = ProjectManager(ROOT)

    # -------------- Welche Projekte?
    if sync_all:
        uids = pm.list_uids()
    elif uid:
        uids = [uid]
    else:
        current = load_current()
        if current is None:
            raise click.ClickException(
                "Keine UID angegeben und kein Projekt ausgewählt.\n"
                "Erst 'glacium projects' + 'glacium select <Nr>'.")
        uids = [current]

    # -------------- Refresh
    for u in uids:
        pm.refresh_jobs(u)
        click.echo(f"{u}: Job-Liste aktualisiert.")

