"""Execute predefined pipeline workflows."""
from __future__ import annotations

from pathlib import Path
import yaml
import click

from glacium.managers.project_manager import ProjectManager
from glacium.pipelines import PipelineManager
from glacium.utils.logging import log_call

ROOT = Path("runs")
DEFAULT_LAYOUT = "grid-convergence"


def _parse_value(v: str):
    try:
        return yaml.safe_load(v)
    except Exception:
        return v


@click.command("pipeline")
@click.option("--layout", default=DEFAULT_LAYOUT, show_default=True, help="Pipeline layout to execute")
@click.option("--level", "levels", multiple=True, type=int, help="Grid refinement levels")
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
@click.option("--pdf/--no-pdf", default=False, help="Merge analysis reports into a summary PDF")
@log_call
def cli_pipeline(
    layout: str,
    levels: tuple[int],
    params: tuple[str],
    output: Path,
    multishots: tuple[str],
    pdf: bool,
):
    """Run a pipeline workflow."""

    pm = ProjectManager(output)
    pipe = PipelineManager.create(layout)

    extra_params: dict[str, object] = {}
    for item in params:
        if "=" not in item:
            raise click.ClickException(f"Invalid --param value: {item}")
        k, v = item.split("=", 1)
        extra_params[k] = _parse_value(v)

    ms_values: list[list[int]] = []
    for seq in multishots:
        try:
            value = eval(seq, {"__builtins__": {}})
        except Exception:
            value = _parse_value(seq)
        if not isinstance(value, list):
            raise click.ClickException(f"Invalid --multishot value: {seq}")
        ms_values.append(value)

    uids, stats = pipe.run(
        pm,
        levels=levels,
        params=extra_params,
        multishots=tuple(ms_values),
    )

    if pdf:
        pipe.merge_pdfs(pm, uids, stats)

    for uid in uids:
        click.echo(uid)


__all__ = ["cli_pipeline"]
