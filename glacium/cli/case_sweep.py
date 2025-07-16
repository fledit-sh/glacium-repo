"""Create multiple projects from parameter sweeps."""

from __future__ import annotations

import itertools
from pathlib import Path
import yaml
import click

from glacium.managers.project_manager import ProjectManager
from glacium.cli.update import cli_update
from glacium.utils.logging import log_call

DEFAULT_RECIPE = "multishot"
DEFAULT_AIRFOIL = Path(__file__).resolve().parents[1] / "data" / "AH63K127.dat"


@click.command("case-sweep")
@click.option(
    "--param",
    "params",
    multiple=True,
    required=True,
    help="KEY=val1,val2,... pairs to sweep",
)
@click.option(
    "-r",
    "--recipe",
    default=DEFAULT_RECIPE,
    show_default=True,
    help="Recipe name or names joined with '+'",
)
@click.option(
    "-o",
    "--output",
    default="runs",
    show_default=True,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path, writable=True),
    help="Root directory for projects",
)
@click.option(
    "--multishots",
    type=int,
    help="Number of MULTISHOT runs",
)
@log_call
def cli_case_sweep(params: tuple[str], recipe: str, output: Path, multishots: int | None) -> None:
    """Create projects for all parameter combinations."""

    def _parse_value(v: str):
        try:
            return yaml.safe_load(v)
        except Exception:
            return v

    param_map: dict[str, list] = {}
    for item in params:
        if "=" not in item:
            raise click.ClickException(f"Invalid --param value: {item}")
        key, values = item.split("=", 1)
        param_map[key] = [_parse_value(x) for x in values.split(",")]

    keys = list(param_map)
    pm = ProjectManager(output)

    for combo in itertools.product(*(param_map[k] for k in keys)):
        proj = pm.create("case", recipe, DEFAULT_AIRFOIL, multishots=multishots)
        proj.config.dump(proj.paths.global_cfg_file())
        case_file = proj.root / "case.yaml"
        case = yaml.safe_load(case_file.read_text()) or {}
        for k, v in zip(keys, combo):
            case[k] = v
        case_file.write_text(yaml.safe_dump(case, sort_keys=False))
        cli_update.callback(proj.uid, None)
        click.echo(proj.uid)


__all__ = ["cli_case_sweep"]
