"""Manage individual jobs within the selected project."""

import click
from pathlib import Path
import yaml
from glacium.utils.current import load
from glacium.managers.ProjectManager import ProjectManager
from glacium.models.job import JobStatus
from rich.console import Console
from rich.table import Table
from rich import box

ROOT = Path("runs")
console = Console()

@click.group("job")
def cli_job():
    """Job-Utilities für das aktuell gewählte Projekt."""
    pass

@cli_job.command("reset")
@click.argument("job_name")
def cli_job_reset(job_name: str):
    """Setzt JOB auf PENDING (falls nicht RUNNING)."""
    uid = load()
    if uid is None:
        raise click.ClickException("Kein Projekt gewählt. Erst 'glacium select' nutzen.")

    pm = ProjectManager(ROOT)
    try:
        proj = pm.load(uid)
    except FileNotFoundError:
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.") from None
    job  = proj.job_manager._jobs.get(job_name.upper())

    if job is None:
        raise click.ClickException(f"Job '{job_name}' existiert nicht.")
    if job.status is JobStatus.RUNNING:
        raise click.ClickException("Job läuft – Reset nicht erlaubt.")

    job.status = JobStatus.PENDING
    proj.job_manager._save_status()
    click.echo(f"{job_name} → PENDING")


@cli_job.command("list")
@click.option("--available", is_flag=True,
              help="Nur die laut Rezept verfügbaren Jobs anzeigen")
def cli_job_list(available: bool):
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
        from glacium.managers.RecipeManager import RecipeManager
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

    for job in proj.jobs:
        st = status_map.get(job.name, "PENDING")
        color = colors.get(st, "")
        table.add_row(job.name, f"[{color}]{st}[/{color}]")

    console.print(table)


@cli_job.command("add")
@click.argument("job_name")
def cli_job_add(job_name: str):
    """Fügt einen Job aus dem aktuellen Rezept hinzu."""
    uid = load()
    if uid is None:
        raise click.ClickException("Kein Projekt gewählt. Erst 'glacium select' nutzen.")

    pm = ProjectManager(ROOT)
    try:
        proj = pm.load(uid)
    except FileNotFoundError:
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.") from None

    from glacium.managers.RecipeManager import RecipeManager
    recipe_jobs = {j.name: j for j in RecipeManager.create(proj.config.recipe).build(proj)}

    jname = job_name.upper()
    if jname not in recipe_jobs:
        raise click.ClickException(f"Job '{job_name}' nicht bekannt.")
    if jname in proj.job_manager._jobs:
        click.echo(f"{jname} existiert bereits.")
        return

    job = recipe_jobs[jname]
    proj.jobs.append(job)
    proj.job_manager._jobs[jname] = job
    proj.job_manager._save_status()
    click.echo(f"{jname} hinzugefügt.")


@cli_job.command("remove")
@click.argument("job_name")
def cli_job_remove(job_name: str):
    """Entfernt einen Job aus dem aktuellen Projekt."""
    uid = load()
    if uid is None:
        raise click.ClickException("Kein Projekt gewählt. Erst 'glacium select' nutzen.")

    pm = ProjectManager(ROOT)
    try:
        proj = pm.load(uid)
    except FileNotFoundError:
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.") from None

    jname = job_name.upper()
    if jname not in proj.job_manager._jobs:
        raise click.ClickException(f"Job '{job_name}' existiert nicht.")

    proj.jobs = [j for j in proj.jobs if j.name != jname]
    del proj.job_manager._jobs[jname]
    proj.job_manager._save_status()
    click.echo(f"{jname} entfernt.")

