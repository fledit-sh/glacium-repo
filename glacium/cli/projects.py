"""List all projects with their job progress."""

import click
from glacium.utils.logging import log_call
from rich.console import Console
from rich.table import Table
from rich import box
from pathlib import Path
from glacium.utils.ProjectIndex import list_projects

@click.command("projects")
@log_call
def cli_projects():
    """Listet alle Projekte mit Job-Fortschritt."""
    console = Console()
    root = Path("runs")
    items = list_projects(root)

    # Sammle alle Keys aus case.yaml
    param_keys: set[str] = set()
    for info in items:
        param_keys.update(info.case_params.keys())

    table = Table(title="Glacium – Projekte", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right")
    table.add_column("UID", overflow="fold")
    table.add_column("Name")
    table.add_column("Jobs")
    table.add_column("Recipe")
    for key in sorted(param_keys):
        table.add_column(key)

    for idx, info in enumerate(items, start=1):
        jobs = f"{info.jobs_done}/{info.jobs_total}" if info.jobs_total else "-"
        values = [str(info.case_params.get(k, "")) for k in sorted(param_keys)]
        table.add_row(str(idx), info.uid, info.name, jobs, info.recipe, *values)

    console.print(table)

if __name__ == "__main__":
    cli_projects()

