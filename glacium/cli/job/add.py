"""Implementation of ``glacium job add``."""

from __future__ import annotations

import click
from glacium.utils.logging import log_call

from glacium.utils.current import load
from glacium.managers.project_manager import ProjectManager
from glacium.managers.config_manager import ConfigManager

from . import cli_job, ROOT


@cli_job.command("add")
@click.argument("job_name")
@log_call
def cli_job_add(job_name: str) -> None:
    """Fügt einen Job aus dem aktuellen Rezept hinzu."""
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

    from glacium.managers.recipe_manager import RecipeManager

    if proj.config.recipe == "CUSTOM":
        recipe_jobs = {}
    else:
        recipe_jobs = {
            j.name: j
            for j in RecipeManager.create(proj.config.recipe).build(proj)
        }

    if job_name.isdigit():
        from glacium.utils import list_jobs

        idx = int(job_name) - 1
        all_jobs = list_jobs()
        if idx < 0 or idx >= len(all_jobs):
            raise click.ClickException("Ungültige Nummer.")
        target = all_jobs[idx]
    else:
        target = job_name.upper()

    added: list[str] = []

    def add_with_deps(name: str) -> None:
        if name in proj.job_manager._jobs or name in added:
            return
        job = recipe_jobs.get(name)
        if job is None:
            from glacium.utils.JobIndex import JobFactory

            if JobFactory.get(name) is None:
                raise click.ClickException(f"Job '{name}' nicht bekannt.")
            job = JobFactory.create(name, proj)
        for dep in getattr(job, "deps", ()):
            add_with_deps(dep)
        proj.jobs.append(job)
        proj.job_manager._jobs[name] = job
        try:
            job.prepare()
        except Exception:
            pass
        added.append(name)

    add_with_deps(target)

    proj.job_manager._save_status()

    proj.config.recipe = "CUSTOM"
    cfg_mgr = ConfigManager(proj.paths)
    cfg = cfg_mgr.load_global()
    cfg.recipe = "CUSTOM"
    cfg_mgr.dump_global()
    cfg_mgr.set("RECIPE", "CUSTOM")

    for jname in added:
        click.echo(f"{jname} hinzugefügt.")
