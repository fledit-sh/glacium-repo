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

    case_table = Table(title="case.yaml", box=box.SIMPLE_HEAVY)
    case_table.add_column("Key")
    case_table.add_column("Value")
    for key, value in case.items():
        case_table.add_row(str(key), str(value))
    console.print(case_table)

    keys = [
        "PROJECT_NAME",
        "PWS_REFINEMENT",
        "FSP_MACH_NUMBER",
        "FSP_REYNOLDS_NUMBER",
        "FSP_FREESTREAM_PRESSURE",
        "FSP_MOMENTS_REFERENCE_POINT_COMPONENT_X",
        "FSP_MOMENTS_REFERENCE_POINT_COMPONENT_Y",
        "FSP_MOMENTS_REFERENCE_POINT_COMPONENT_Z",
        "FSP_CHARAC_LENGTH",
        "ICE_CHARAC_LENGTH",
        "ICE_REF_AIR_PRESSURE",
        "ICE_REF_TEMPERATURE",
        "ICE_TEMPERATURE",
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
