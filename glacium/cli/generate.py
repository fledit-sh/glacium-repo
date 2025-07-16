"""Generate a global config from a case description."""

from __future__ import annotations

from pathlib import Path
import yaml
import click

from glacium.utils.logging import log_call
from glacium.utils import generate_global_defaults
from glacium.utils.default_paths import global_default_config


@click.command("generate")
@click.argument("case_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Write YAML to file instead of stdout",
)
@log_call
def cli_generate(case_file: Path, output: Path | None) -> None:
    """Create ``global_config`` values from ``case_file``."""
    cfg = generate_global_defaults(case_file, global_default_config())
    text = yaml.safe_dump(cfg, sort_keys=False)
    if output:
        output.write_text(text)
        click.echo(str(output))
    else:
        click.echo(text)


__all__ = ["cli_generate"]
