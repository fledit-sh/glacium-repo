"""List all projects with their job progress."""

import click
from glacium.utils.logging import log_call
from rich.console import Console
from rich.table import Table
from rich import box
from pathlib import Path
from glacium.utils.ProjectIndex import list_projects
from glacium.utils.convergence import execution_time, cl_cd_summary


def _format_time(seconds: float) -> str:
    """Return ``HH:MM:SS`` string for ``seconds``."""

    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:05.2f}"

@click.command("projects")
@click.option("--results", is_flag=True, help="Show solver results")
@log_call
def cli_projects(results: bool):
    """Listet alle Projekte mit Job-Fortschritt."""
    console = Console()
    root = Path("runs")
    items = list_projects(root)

    # Sammle alle Keys aus case.yaml
    param_keys: set[str] = set()
    for info in items:
        param_keys.update(info.case_params.keys())

    table = Table(title="Glacium – Projekte", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right")
    table.add_column("UID", overflow="fold")
    table.add_column("Name")
    table.add_column("Jobs")
    table.add_column("Recipe")
    if results:
        table.add_column("Time", justify="right")
        table.add_column("CL mean", justify="right")
        table.add_column("CL σ", justify="right")
        table.add_column("CD mean", justify="right")
        table.add_column("CD σ", justify="right")
    for key in sorted(param_keys):
        table.add_column(key)

    for idx, info in enumerate(items, start=1):
        jobs = f"{info.jobs_done}/{info.jobs_total}" if info.jobs_total else "-"
        values = [str(info.case_params.get(k, "")) for k in sorted(param_keys)]
        extra: list[str] = []
        if results:
            out_file = None
            for d in ("run_MULTISHOT", "run_FENSAP", "run_DROP3D", "run_ICE3D"):
                f = info.path / d / ".solvercmd.out"
                if f.exists():
                    out_file = f
                    break
            if out_file:
                secs = execution_time(out_file)
                t = _format_time(secs)
                cl_mean, cl_std, cd_mean, cd_std = cl_cd_summary(out_file.parent)
                if cl_mean != cl_mean:  # NaN check
                    extra = [t, "-", "-", "-", "-"]
                else:
                    extra = [
                        t,
                        f"{cl_mean:.3f}",
                        f"{cl_std:.3f}",
                        f"{cd_mean:.3f}",
                        f"{cd_std:.3f}",
                    ]
            else:
                extra = ["-", "-", "-", "-", "-"]
        table.add_row(str(idx), info.uid, info.name, jobs, info.recipe, *extra, *values)

    console.print(table)

if __name__ == "__main__":
    cli_projects()

