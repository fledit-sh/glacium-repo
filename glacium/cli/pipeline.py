"""Grid convergence pipeline helper."""
from __future__ import annotations

from pathlib import Path
import yaml
import click

from glacium.managers.project_manager import ProjectManager
from glacium.managers.job_manager import JobManager
from glacium.utils.logging import log_call
from glacium.utils.convergence import project_cl_cd_stats
from .update import cli_update

DEFAULT_AIRFOIL = Path(__file__).resolve().parents[1] / "data" / "AH63K127.dat"
ROOT = Path("runs")


def _parse_value(v: str):
    try:
        return yaml.safe_load(v)
    except Exception:
        return v


@click.command("pipeline")
@click.option("--level", "levels", multiple=True, required=True, type=int, help="Grid refinement levels")
@click.option("--param", "params", multiple=True, help="Additional case.yaml parameters KEY=VALUE")
@click.option(
    "-o",
    "--output",
    default=ROOT,
    show_default=True,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path, writable=True),
    help="Root directory for projects",
)
@click.option("--multishot", "multishots", multiple=True, help="Multishot sequences after grid selection")
@log_call
def cli_pipeline(levels: tuple[int], params: tuple[str], output: Path, multishots: tuple[str]):
    """Run grid convergence and prepare follow-up projects."""

    pm = ProjectManager(output)

    extra_params: dict[str, object] = {}
    for item in params:
        if "=" not in item:
            raise click.ClickException(f"Invalid --param value: {item}")
        k, v = item.split("=", 1)
        extra_params[k] = _parse_value(v)

    grid_projs: list[tuple[int, str]] = []
    stats: list[tuple[str, float, float]] = []

    for level in levels:
        proj = pm.create("grid", "grid_dep", DEFAULT_AIRFOIL)
        case_file = proj.root / "case.yaml"
        case = yaml.safe_load(case_file.read_text()) or {}
        case.update(extra_params)
        case["PWS_REFINEMENT"] = level
        case_file.write_text(yaml.safe_dump(case, sort_keys=False))
        cli_update.callback(proj.uid, None)
        JobManager(proj).run()
        cl_mean, cl_std, cd_mean, cd_std = project_cl_cd_stats(proj.root / "run_FENSAP")
        grid_projs.append((level, proj.uid))
        stats.append((proj.uid, cl_mean, cd_mean))

    if not stats:
        raise click.ClickException("no projects created")

    best_uid, _, best_cd = min(stats, key=lambda x: x[2])
    best_level = [lvl for lvl, uid in grid_projs if uid == best_uid][0]

    click.echo(f"Best grid: {best_level}")

    follow_uids: list[str] = []
    proj = pm.create("single", "prep+solver", DEFAULT_AIRFOIL)
    case_file = proj.root / "case.yaml"
    case = yaml.safe_load(case_file.read_text()) or {}
    case.update(extra_params)
    case["PWS_REFINEMENT"] = best_level
    case_file.write_text(yaml.safe_dump(case, sort_keys=False))
    cli_update.callback(proj.uid, None)
    follow_uids.append(proj.uid)

    for seq in multishots:
        try:
            value = eval(seq, {"__builtins__": {}})
        except Exception:
            value = _parse_value(seq)
        if not isinstance(value, list):
            raise click.ClickException(f"Invalid --multishot value: {seq}")
        proj = pm.create("multishot", "prep+solver", DEFAULT_AIRFOIL)
        case_file = proj.root / "case.yaml"
        case = yaml.safe_load(case_file.read_text()) or {}
        case.update(extra_params)
        case["PWS_REFINEMENT"] = best_level
        case["CASE_MULTISHOT"] = value
        case_file.write_text(yaml.safe_dump(case, sort_keys=False))
        cli_update.callback(proj.uid, None)
        follow_uids.append(proj.uid)

    for _, uid in grid_projs:
        click.echo(uid)
    for uid in follow_uids:
        click.echo(uid)


__all__ = ["cli_pipeline"]
