"""Parameter sweep for grid dependency recipe."""

from __future__ import annotations

from pathlib import Path
import yaml
import click
from contextlib import redirect_stdout
import io

from glacium.utils.logging import log_call
from glacium.managers.project_manager import ProjectManager
from .update import cli_update

ROOT = Path("runs")
DEFAULT_AIRFOIL = Path(__file__).resolve().parents[1] / "data" / "AH63K127.dat"


@click.command("sweep")
@click.argument("start", type=float)
@click.option("-n", "--steps", default=8, show_default=True, type=int,
              help="Number of iterations")
@click.option("-f", "--factor", default=2.0, show_default=True, type=float,
              help="Multiplication factor")
@click.option("--run/--no-run", "do_run", default=False, show_default=True,
              help="Execute jobs after creation")
@log_call
def cli_sweep(start: float, steps: int, factor: float, do_run: bool) -> None:
    """Create projects for various ``PWS_REFINEMENT`` values."""
    pm = ProjectManager(ROOT)
    value = start
    for _ in range(steps):
        proj = pm.create(f"sweep-{value}", "grid_dep", DEFAULT_AIRFOIL)
        uid = proj.uid
        with io.StringIO() as buf, redirect_stdout(buf):
            cli_update.callback(uid, None)
        cfg_file = proj.paths.global_cfg_file()
        cfg = yaml.safe_load(cfg_file.read_text()) or {}
        cfg["PWS_REFINEMENT"] = value
        cfg_file.write_text(yaml.safe_dump(cfg, sort_keys=False))
        click.echo(uid)
        if do_run:
            pm.load(uid).job_manager.run()
        value *= factor


__all__ = ["cli_sweep"]
