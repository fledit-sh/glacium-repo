"""Implementation of ``glacium job select``."""

from __future__ import annotations

import click
from glacium.utils.logging import log_call

from glacium.utils.current import load
from glacium.managers.project_manager import ProjectManager

from . import cli_job, ROOT


@cli_job.command("select")
@click.argument("job")
@log_call
def cli_job_select(job: str) -> None:
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
