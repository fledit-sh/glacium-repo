from __future__ import annotations

from glacium.models.job import Job
from glacium.engines.py_engine import PyEngine
from glacium.utils.convergence import analysis_file
from glacium.utils.report_converg_fensap import build_report


class FensapConvergenceStatsJob(Job):
    """Generate convergence plots for a FENSAP run."""

    name = "FENSAP_CONVERGENCE_STATS"
    deps = ("FENSAP_RUN",)

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        converg_file = project_root / "run_FENSAP" / "converg"
        out_dir = project_root / "analysis" / "FENSAP"

        engine = PyEngine(analysis_file)
        engine.run([converg_file, out_dir], cwd=project_root)

        stats_file = out_dir / "stats.csv"
        if stats_file.exists():
            import csv
            import yaml

            from glacium.utils import normalise_key

            with stats_file.open() as fh:
                rows = csv.DictReader(fh)
                results = {normalise_key(r["label"]): float(r["mean"]) for r in rows}

            res_path = project_root / "results.yaml"
            if res_path.exists():
                existing = yaml.safe_load(res_path.read_text()) or {}
            else:
                existing = {}
            existing.update(results)
            res_path.write_text(yaml.safe_dump(existing, sort_keys=False))

        if self.project.config.get("CONVERGENCE_PDF"):
            build_report(out_dir)
