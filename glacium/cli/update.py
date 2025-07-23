"""Refresh ``global_config.yaml`` from ``case.yaml``.

Existing values from an earlier configuration are preserved so custom
modifications like ``RECIPE`` or ``PROJECT_NAME`` remain intact.
"""

from __future__ import annotations

from pathlib import Path
import click

from glacium.utils.logging import log_call
from glacium.utils.current import load as load_current
from glacium.managers.project_manager import ProjectManager
from glacium.services import ProjectService

ROOT = Path("runs")


@click.command("update")
@click.argument("uid", required=False)
@click.option(
    "-c",
    "--case",
    "case_file",
    type=click.Path(exists=True, path_type=Path),
    help="case.yaml to read instead of <project>/case.yaml",
)
@log_call
def cli_update(uid: str | None, case_file: Path | None) -> None:
    """Regenerate ``global_config.yaml`` for a project."""
    pm = ProjectManager(ROOT)

    if uid is None:
        uid = load_current()
        if uid is None:
            raise click.ClickException(
                "Keine UID angegeben und kein Projekt ausgewählt.\n"
                "Erst 'glacium projects' + 'glacium select <Nr>'."
            )

    try:
        pm.load(uid)
    except FileNotFoundError:
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.") from None

    service = ProjectService(ROOT)
    dest = service.update_config(uid, case_file)
    click.echo(str(dest))


__all__ = ["cli_update"]
