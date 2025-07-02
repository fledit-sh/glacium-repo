"""List all projects with their job progress."""

import click
from rich import box
from rich.console import Console
from rich.table import Table

from glacium.constants import RUNS_DIR
from glacium.utils.ProjectIndex import list_projects

console = Console()


@click.command("projects")
def cli_projects():
    """Listet alle Projekte mit Job-Fortschritt."""
    table = Table(title="Glacium – Projekte", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right")
    table.add_column("UID", overflow="fold")
    table.add_column("Name")
    table.add_column("Jobs")

    root = RUNS_DIR
    for idx, info in enumerate(list_projects(root), start=1):
        jobs = f"{info.jobs_done}/{info.jobs_total}" if info.jobs_total else "-"
        table.add_row(str(idx), info.uid, info.name, jobs)

    console.print(table)


if __name__ == "__main__":
    cli_projects()
