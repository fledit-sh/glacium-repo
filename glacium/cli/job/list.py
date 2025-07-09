"""Implementation of ``glacium job list``."""

from __future__ import annotations

import yaml
import click
from glacium.utils.logging import log_call
from rich.table import Table
from rich import box

from glacium.utils.current import load
from glacium.managers.project_manager import ProjectManager

from . import cli_job, ROOT, console


@cli_job.command("list")
@click.option("--available", is_flag=True, help="Nur die laut Rezept verfügbaren Jobs anzeigen")
@log_call
def cli_job_list(available: bool) -> None:
    """Zeigt alle Jobs + Status des aktuellen Projekts."""
    uid = load()
    if uid is None:
        raise click.ClickException("Kein Projekt gewählt. Erst 'glacium select' nutzen.")

    pm = ProjectManager(ROOT)
    try:
        proj = pm.load(uid)
    except FileNotFoundError:
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.") from None

    if available:
        if proj.config.recipe == "CUSTOM":
            from glacium.utils.JobIndex import JobFactory

            for name in JobFactory.list():
                click.echo(name)
            return

        from glacium.managers.recipe_manager import RecipeManager

        recipe = RecipeManager.create(proj.config.recipe)
        for job in recipe.build(proj):
            click.echo(job.name)
        return

    status_file = proj.paths.cfg_dir() / "jobs.yaml"
    if status_file.exists():
        status_map = yaml.safe_load(status_file.read_text()) or {}
    else:
        status_map = {j.name: j.status.name for j in proj.jobs}

    table = Table(title=f"Glacium – Job-Status [{uid}]", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right")
    table.add_column("Job", style="bold")
    table.add_column("Status")

    colors = {
        "DONE": "green",
        "FAILED": "red",
        "RUNNING": "yellow",
        "SKIPPED": "grey62",
        "STALE": "magenta",
        "PENDING": "bright_black",
    }

    for idx, job in enumerate(proj.jobs, start=1):
        st = status_map.get(job.name, "PENDING")
        color = colors.get(st, "")
        table.add_row(str(idx), job.name, f"[{color}]{st}[/{color}]")

    console.print(table)
