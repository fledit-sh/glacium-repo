"""glacium.cli.new
===================
CLI-Befehl `glacium new` – legt ein frisches Projekt an.

Funktionen
----------
• UID-Ordner in *runs/* erstellen
• Default-GlobalConfig kopieren (oder Minimal-Fallback)
• Airfoil-Datei ins Projekt kopieren und Pfad in Config setzen
• Alle Templates einmalig rendern
• Recipe auswählen → Jobs erzeugen → jobs.yaml schreiben
"""
from __future__ import annotations

from pathlib import Path

import click

from glacium.utils.logging import log, log_call
from glacium.managers.project_manager import ProjectManager

# Paket-Ressourcen ---------------------------------------------------------
PKG_ROOT = Path(__file__).resolve().parents[2]
PKG_PKG = Path(__file__).resolve().parents[1]
RUNS_ROOT = PKG_ROOT / "runs"

DEFAULT_RECIPE = "multishot"
DEFAULT_AIRFOIL = PKG_PKG / "data" / "AH63K127.dat"

# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
# Click-Command
# ------------------------------------------------------------------------
@click.command("new")
@click.argument("name")
@click.option("-a", "--airfoil",
              type=click.Path(path_type=Path),
              default=DEFAULT_AIRFOIL,
              show_default=True,
              help="Pfad zur Profil-Datei")
@click.option("-r", "--recipe",
              default=DEFAULT_RECIPE,
              show_default=True,
              help="Name des Rezepts (Jobs)")
@click.option("-o", "--output", default=str(RUNS_ROOT), show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=Path),
              help="Root-Ordner für Projekte")
@click.option("-y", "--yes", is_flag=True,
              help="Existierenden Ordner ohne Rückfrage überschreiben")
@log_call
def cli_new(name: str, airfoil: Path, recipe: str, output: Path, yes: bool) -> None:
    """Erstellt ein neues Glacium-Projekt."""

    pm = ProjectManager(output)
    project = pm.create(name, recipe, airfoil)
    log.success(f"Projekt angelegt: {project.root}")
    click.echo(project.uid)


if __name__ == "__main__":
    cli_new()
