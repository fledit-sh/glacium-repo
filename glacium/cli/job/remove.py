"""Implementation of ``glacium job remove``."""

from __future__ import annotations

import click
from glacium.utils.logging import log_call

from glacium.utils.current import load
from glacium.managers.project_manager import ProjectManager
from glacium.managers.config_manager import ConfigManager

from . import cli_job, ROOT


@cli_job.command("remove")
@click.argument("job_name")
@log_call
def cli_job_remove(job_name: str) -> None:
    """Entfernt einen Job aus dem aktuellen Projekt."""
    uid = load()
    if uid is None:
        raise click.ClickException(
            "Kein Projekt gewählt. Erst 'glacium select' nutzen."
        )

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

    proj.config.recipe = "CUSTOM"
    cfg_mgr = ConfigManager(proj.paths)
    cfg = cfg_mgr.load_global()
    cfg.recipe = "CUSTOM"
    cfg_mgr.dump_global()
    cfg_mgr.set("RECIPE", "CUSTOM")

    click.echo(f"{jname} entfernt.")
