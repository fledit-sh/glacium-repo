from __future__ import annotations

from pathlib import Path
import yaml
import click

from glacium.pipelines.pipeline_manager import BasePipeline, PipelineManager
from glacium.managers.project_manager import ProjectManager
from glacium.managers.job_manager import JobManager
from glacium.utils.convergence import project_cl_cd_stats
from glacium.cli.update import cli_update


@PipelineManager.register
class GridConvergencePipeline(BasePipeline):
    """Grid convergence workflow with follow-up projects."""

    name = "grid-convergence"
    description = "Run grid convergence study and spawn follow-up projects"

    def run(
        self,
        pm: ProjectManager,
        levels: tuple[int],
        params: dict[str, object] | None = None,
        multishots: tuple[list[int], ...] = (),
    ) -> tuple[list[str], list[tuple[str, float, float, float, float]]]:
        params = params or {}
        default_airfoil = Path(__file__).resolve().parents[1] / "data" / "AH63K127.dat"

        grid_projs: list[tuple[int, str]] = []
        stats: list[tuple[str, float, float, float, float]] = []

        for level in levels:
            proj = pm.create("grid", "grid_dep", default_airfoil)
            case_file = proj.root / "case.yaml"
            case = yaml.safe_load(case_file.read_text()) or {}
            case.update(params)
            case["PWS_REFINEMENT"] = level
            case_file.write_text(yaml.safe_dump(case, sort_keys=False))
            cli_update.callback(proj.uid, None)
            JobManager(proj).run()
            cl_mean, cl_std, cd_mean, cd_std = project_cl_cd_stats(proj.root / "run_FENSAP")
            grid_projs.append((level, proj.uid))
            stats.append((proj.uid, cl_mean, cl_std, cd_mean, cd_std))

        if not stats:
            raise click.ClickException("no projects created")

        best_uid, _, _, best_cd, _ = min(stats, key=lambda x: x[3])
        best_level = [lvl for lvl, uid in grid_projs if uid == best_uid][0]

        click.echo(f"Best grid: {best_level}")

        follow_uids: list[str] = []
        proj = pm.create("single", "prep+solver", default_airfoil)
        case_file = proj.root / "case.yaml"
        case = yaml.safe_load(case_file.read_text()) or {}
        case.update(params)
        case["PWS_REFINEMENT"] = best_level
        case_file.write_text(yaml.safe_dump(case, sort_keys=False))
        cli_update.callback(proj.uid, None)
        JobManager(proj).run()
        stats.append((proj.uid, *project_cl_cd_stats(proj.root / "run_FENSAP")))
        follow_uids.append(proj.uid)

        for seq in multishots:
            proj = pm.create("multishot", "multishot", default_airfoil)
            case_file = proj.root / "case.yaml"
            case = yaml.safe_load(case_file.read_text()) or {}
            case.update(params)
            case["PWS_REFINEMENT"] = best_level
            case["CASE_MULTISHOT"] = list(seq)
            case_file.write_text(yaml.safe_dump(case, sort_keys=False))
            cli_update.callback(proj.uid, None)
            JobManager(proj).run()
            stats.append((proj.uid, *project_cl_cd_stats(proj.root / "run_MULTISHOT")))
            follow_uids.append(proj.uid)

        uids = [uid for _, uid in grid_projs] + follow_uids
        return uids, stats


__all__ = ["GridConvergencePipeline"]
