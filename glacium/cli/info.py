"""Show configuration details for a project."""

from __future__ import annotations

from pathlib import Path
import yaml
import click
from glacium.utils.logging import log_call
from rich.console import Console
from rich.table import Table
from rich import box

from glacium.managers.project_manager import ProjectManager
from glacium.utils.current import load as load_current

ROOT = Path("runs")
console = Console()


@click.command("info")
@click.argument("uid", required=False)
@log_call
def cli_info(uid: str | None) -> None:
    """Print case parameters and selected global config values."""
    pm = ProjectManager(ROOT)

    if uid is None:
        uid = load_current()
        if uid is None:
            raise click.ClickException(
                "Kein Projekt ausgewaehlt. Erst 'glacium select <Nr>' nutzen."
            )

    try:
        proj = pm.load(uid)
    except FileNotFoundError:
        raise click.ClickException(f"Projekt '{uid}' nicht gefunden.") from None

    case_file = proj.root / "case.yaml"
    case = yaml.safe_load(case_file.read_text()) if case_file.exists() else {}

    console.print(f"[bold]case.yaml[/bold] ({case_file})")
    console.print(yaml.safe_dump(case, sort_keys=False))

    keys = [
        "PROJECT_NAME",
        "PWS_REFINEMENT",
        "FSP_MACH_NUMBER",
        "ICE_REF_VELOCITY",
    ]
    cfg = proj.config
    table = Table(title="global_config", box=box.SIMPLE_HEAVY)
    table.add_column("Key")
    table.add_column("Value")
    for k in keys:
        if k in cfg:
            table.add_row(k, str(cfg.get(k)))
    console.print(table)


__all__ = ["cli_info"]
