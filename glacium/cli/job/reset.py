"""Implementation of ``glacium job reset``."""

from __future__ import annotations

import click
from glacium.utils.logging import log_call

from glacium.utils.current import load
from glacium.managers.project_manager import ProjectManager
from glacium.models.job import JobStatus

from . import cli_job, ROOT


@cli_job.command("reset")
@click.argument("job_name")
@log_call
def cli_job_reset(job_name: str) -> None:
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
    click.echo(f"{jname} -> PENDING")
