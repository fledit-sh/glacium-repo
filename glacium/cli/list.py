"""Display jobs of a project in a table."""

from pathlib import Path
import yaml
import click
from glacium.utils.logging import log_call
from rich.console import Console
from rich.table import Table
from rich import box

from glacium.managers.project_manager import ProjectManager
from glacium.utils.current import load as load_current
from glacium.models.job import UnavailableJob

console = Console()

@click.command("list")
@click.argument("uid", required=False)
@log_call
def cli_list(uid: str | None):
    """Zeigt alle Jobs + Status fuer ein Projekt.

    Ohne UID wird das aktuell ausgewaehlte Projekt verwendet.
    """
    pm = ProjectManager(Path("runs"))

    if uid is None:
        uid = load_current()
        if uid is None:
            raise click.ClickException(
                "Kein Projekt ausgewaehlt. Erst 'glacium select <Nr>' nutzen."
            )

    try:
        proj = pm.load(uid)  # rekonstruiert Jobs & Manager
    except FileNotFoundError:
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.") from None

    # Status-Map zusammenstellen (JobManager speichert sie als YAML)
    status_file = proj.paths.cfg_dir() / "jobs.yaml"
    if status_file.exists():
        status_map = yaml.safe_load(status_file.read_text()) or {}
    else:
        status_map = {j.name: j.status.name for j in proj.jobs}

    # hübsche Tabelle
    table = Table(title=f"Glacium – Job-Status [{uid}]", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right")
    table.add_column("Job",    style="bold")
    table.add_column("Status")

    colors = {
        "DONE":    "green",
        "FAILED":  "red",
        "RUNNING": "yellow",
        "SKIPPED": "grey62",
        "STALE":   "magenta",
        "PENDING": "bright_black",
    }

    for idx, job in enumerate(proj.jobs, start=1):
        st = status_map.get(job.name, "PENDING")
        name = job.name
        if isinstance(job, UnavailableJob):
            name += " (missing dependency)"
        table.add_row(str(idx), name, f"[{colors.get(st, '')}]{st}[/{colors.get(st, '')}]")

    console.print(table)

# standalone test
if __name__ == "__main__":
    cli_list()

