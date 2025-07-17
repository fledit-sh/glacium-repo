"""Create a default project in the current directory."""
from pathlib import Path
import click
from glacium.utils.logging import log_call

from glacium.api import Run

DEFAULT_NAME = "project"
DEFAULT_RECIPE = "prep"
DEFAULT_AIRFOIL = Path(__file__).resolve().parents[1] / "data" / "AH63K127.dat"

@click.command("init")
@click.option("-n", "--name", default=DEFAULT_NAME, show_default=True,
              help="Name of the project")
@click.option("-r", "--recipe", default=DEFAULT_RECIPE, show_default=True,
              help="Recipe to use")
@click.option("-o", "--output", default="runs", show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, path_type=Path,
                              writable=True),
              help="Root directory for projects")
@log_call
def cli_init(name: str, recipe: str, output: Path) -> None:
    """Create a new project below ``output`` using default settings."""

    run = Run(output)
    run.name(name).select_airfoil(DEFAULT_AIRFOIL)
    run.set("recipe", recipe)
    project = run.create()
    click.echo(project.uid)
