"""Manage individual jobs within the selected project."""

import click
import yaml
from glacium.constants import RUNS_DIR
from glacium.utils.current import load
from glacium.managers.ProjectManager import ProjectManager
from glacium.models.job import JobStatus
from rich.console import Console
from rich.table import Table
from rich import box

ROOT = RUNS_DIR
console = Console()

@click.group("job", invoke_without_command=True)
@click.option(
    "--list",
    "list_all",
    is_flag=True,
    help="Alle implementierten Jobs auflisten",
)
@click.pass_context
def cli_job(ctx: click.Context, list_all: bool):
    """Job-Utilities für das aktuell gewählte Projekt."""

    if ctx.invoked_subcommand is None:
        if list_all:
            from glacium.utils import list_jobs

            for idx, name in enumerate(list_jobs(), start=1):
                click.echo(f"{idx:2d}) {name}")
        else:
            click.echo(ctx.get_help())

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

    if job_name.isdigit():
        idx = int(job_name) - 1
        if idx < 0 or idx >= len(proj.jobs):
            raise click.ClickException("Ungültige Nummer.")
        jname = proj.jobs[idx].name
    else:
        jname = job_name.upper()

    job = proj.job_manager._jobs.get(jname)

    if job is None:
        raise click.ClickException(f"Job '{job_name}' existiert nicht.")
    if job.status is JobStatus.RUNNING:
        raise click.ClickException("Job läuft – Reset nicht erlaubt.")

    job.status = JobStatus.PENDING
    proj.job_manager._save_status()
    click.echo(f"{jname} → PENDING")


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


@cli_job.command("add")
@click.argument("job_name", required=False)
@click.option("-r", "--recipe", "recipe_name",
              help="Jobs aus diesem Rezept hinzufügen")
def cli_job_add(job_name: str | None, recipe_name: str | None):
    """Fügt einen Job oder ein Rezept zum Projekt hinzu."""
    uid = load()
    if uid is None:
        raise click.ClickException("Kein Projekt gewählt. Erst 'glacium select' nutzen.")

    pm = ProjectManager(ROOT)
    try:
        proj = pm.load(uid)
    except FileNotFoundError:
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.") from None

    from glacium.managers.RecipeManager import RecipeManager
    base_recipe = recipe_name or proj.config.recipe
    recipe_obj = RecipeManager.create(base_recipe)
    recipe_jobs_list = recipe_obj.build(proj)
    recipe_jobs = {j.name: j for j in recipe_jobs_list}

    if recipe_name:
        targets = [j.name for j in recipe_jobs_list]
    else:
        if job_name is None:
            raise click.ClickException("JOB_NAME fehlt")
        if job_name.isdigit():
            from glacium.utils import list_jobs

            idx = int(job_name) - 1
            all_jobs = list_jobs()
            if idx < 0 or idx >= len(all_jobs):
                raise click.ClickException("Ungültige Nummer.")
            targets = [all_jobs[idx]]
        else:
            targets = [job_name.upper()]

    added: list[str] = []

    def add_with_deps(name: str) -> None:
        if name in proj.job_manager._jobs or name in added:
            return
        job = recipe_jobs.get(name)
        if job is None:
            from glacium.utils.JobIndex import create_job, get_job_class
            if get_job_class(name) is None:
                raise click.ClickException(f"Job '{name}' nicht bekannt.")
            job = create_job(name, proj)
        for dep in getattr(job, "deps", ()):
            add_with_deps(dep)
        proj.jobs.append(job)
        proj.job_manager._jobs[name] = job
        added.append(name)

    for target in targets:
        add_with_deps(target)

    proj.job_manager._save_status()
    for jname in added:
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

    if job_name.isdigit():
        idx = int(job_name) - 1
        if idx < 0 or idx >= len(proj.jobs):
            raise click.ClickException("Ungültige Nummer.")
        jname = proj.jobs[idx].name
    else:
        jname = job_name.upper()
        if jname not in proj.job_manager._jobs:
            raise click.ClickException(f"Job '{job_name}' existiert nicht.")

    proj.jobs = [j for j in proj.jobs if j.name != jname]
    del proj.job_manager._jobs[jname]
    proj.job_manager._save_status()
    click.echo(f"{jname} entfernt.")


@cli_job.command("run")
@click.argument("job_name")
def cli_job_run(job_name: str):
    """Führe JOB aus dem aktuellen Projekt aus."""
    uid = load()
    if uid is None:
        raise click.ClickException("Kein Projekt gewählt. Erst 'glacium select' nutzen.")

    pm = ProjectManager(ROOT)
    try:
        proj = pm.load(uid)
    except FileNotFoundError:
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.") from None

    if job_name.isdigit():
        idx = int(job_name) - 1
        if idx < 0 or idx >= len(proj.jobs):
            raise click.ClickException("Ungültige Nummer.")
        jname = proj.jobs[idx].name
    else:
        jname = job_name.upper()
        if jname not in proj.job_manager._jobs:
            raise click.ClickException(f"Job '{job_name}' existiert nicht.")

    job = proj.job_manager._jobs[jname]
    if job.status is JobStatus.RUNNING:
        raise click.ClickException("Job läuft bereits.")
    job.status = JobStatus.PENDING
    proj.job_manager._save_status()

    proj.job_manager.run([jname])


@cli_job.command("select")
@click.argument("job")
def cli_job_select(job: str):
    """Wähle JOB innerhalb des aktuellen Projekts aus."""
    uid = load()
    if uid is None:
        raise click.ClickException("Kein Projekt gewählt. Erst 'glacium select' nutzen.")

    pm = ProjectManager(ROOT)
    try:
        proj = pm.load(uid)
    except FileNotFoundError:
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.") from None

    if job.isdigit():
        idx = int(job) - 1
        if idx < 0 or idx >= len(proj.jobs):
            raise click.ClickException("Ungültige Nummer.")
        jname = proj.jobs[idx].name
    else:
        jname = job.upper()
        if jname not in proj.job_manager._jobs:
            raise click.ClickException(f"Job '{job}' existiert nicht.")

    from glacium.utils.current_job import save as save_job

    save_job(jname)
    click.echo(jname)

