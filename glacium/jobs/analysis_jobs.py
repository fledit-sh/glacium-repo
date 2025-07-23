"""Job classes performing post-processing analysis."""

from glacium.models.job import Job
from glacium.engines.py_engine import PyEngine
from glacium.utils.convergence import analysis, analysis_file
from glacium.utils.report_converg_fensap import build_report
from glacium.utils.mesh_analysis import mesh_analysis
from glacium.utils.postprocess_fensap import fensap_analysis
from glacium.post import analysis as post_analysis
import pandas as pd
import os


class ConvergenceStatsJob(Job):
    """Aggregate convergence statistics of a MULTISHOT run."""

    name = "CONVERGENCE_STATS"
    deps = ("MULTISHOT_RUN",)

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        report_dir = project_root / "run_MULTISHOT"
        out_dir = project_root / "analysis" / "MULTISHOT"

        engine = PyEngine(analysis)
        engine.run([report_dir, out_dir], cwd=project_root)

        if self.project.config.get("CONVERGENCE_PDF"):
            files = sorted(report_dir.glob("converg.fensap.*"))
            if files:
                PyEngine(analysis_file).run([files[-1], out_dir], cwd=project_root)
            build_report(out_dir)


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


class Drop3dConvergenceStatsJob(Job):
    """Generate convergence plots for a DROP3D run."""

    name = "DROP3D_CONVERGENCE_STATS"
    deps = ("DROP3D_RUN",)

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        converg_file = project_root / "run_DROP3D" / "converg"
        out_dir = project_root / "analysis" / "DROP3D"

        engine = PyEngine(analysis_file)
        engine.run([converg_file, out_dir], cwd=project_root)

        if self.project.config.get("CONVERGENCE_PDF"):
            build_report(out_dir)


class Ice3dConvergenceStatsJob(Job):
    """Generate convergence plots for an ICE3D run."""

    name = "ICE3D_CONVERGENCE_STATS"
    deps = ("ICE3D_RUN",)

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        converg_file = project_root / "run_ICE3D" / "iceconv.dat"
        out_dir = project_root / "analysis" / "ICE3D"

        engine = PyEngine(analysis_file)
        engine.run([converg_file, out_dir], cwd=project_root)

        if self.project.config.get("CONVERGENCE_PDF"):
            build_report(out_dir)


class AnalyzeMultishotJob(Job):
    """Analyse MULTISHOT solver exports."""

    name = "ANALYZE_MULTISHOT"
    deps = ("POSTPROCESS_MULTISHOT",)

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        run_dir = project_root / "run_MULTISHOT"
        out_dir = project_root / "analysis" / "MULTISHOT"
        out_dir.mkdir(parents=True, exist_ok=True)

        cfg = self.project.config
        p_inf = float(cfg.get("FSP_FREESTREAM_PRESSURE", 101325.0))
        t_inf = float(cfg.get("FSP_FREESTREAM_TEMPERATURE", 288.0))
        u_inf = float(cfg.get("FSP_FREESTREAM_VELOCITY", 0.0))
        chord = float(cfg.get("FSP_CHARAC_LENGTH", 1.0))
        rho_inf = p_inf / (287.05 * t_inf)

        wall_tol = float(cfg.get("CP_WALL_TOL", 1e-4))
        rel_pct = float(cfg.get("CP_REL_PCT", 2.0))

        cp_results: list[tuple[str, pd.DataFrame]] = []
        for dat in sorted(run_dir.glob("soln.fensap.??????.dat")):
            df = post_analysis.read_tec_ascii(dat)
            cp = post_analysis.compute_cp(
                df,
                p_inf,
                rho_inf,
                u_inf,
                chord,
                wall_tol,
                rel_pct,
            )
            cp_results.append((dat.stem, cp))
            img = out_dir / f"{dat.stem}_cp.png"
            post_analysis.plot_cp_directional(
                dat,
                p_inf,
                rho_inf,
                u_inf,
                chord,
                img,
            )

        if cp_results:
            post_analysis.plot_cp_overlay(cp_results, out_dir / "all_cp.png")

        for dat in sorted(run_dir.glob("swimsol.ice.??????.dat")):
            df = post_analysis.read_wall_zone(dat)
            proc, unit = post_analysis.process_wall_zone(df, chord=chord, unit="mm")
            img = out_dir / f"{dat.stem}_ice.png"
            post_analysis.plot_ice_thickness(proc, unit, img)

        cwd = os.getcwd()
        os.chdir(run_dir)
        try:
            segments = post_analysis.load_contours("*.stl")
        finally:
            os.chdir(cwd)
        post_analysis.animate_growth(segments, out_dir / "ice_growth.gif")


class FensapAnalysisJob(Job):
    """Generate slice plots from FENSAP results."""

    name = "FENSAP_ANALYSIS"
    deps = ("POSTPROCESS_SINGLE_FENSAP",)

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        dat_file = project_root / "run_FENSAP" / "soln.fensap.dat"
        out_dir = project_root / "analysis" / "FENSAP"

        engine = PyEngine(fensap_analysis)
        engine.run([dat_file, out_dir], cwd=project_root)


class MeshAnalysisJob(Job):
    """Generate mesh screenshots and HTML report."""

    name = "MESH_ANALYSIS"
    deps: tuple[str, ...] = ()

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        meshfile = project_root / "run_MULTISHOT" / "lastwrap-remeshed.msh"
        out_dir = project_root / "analysis" / "MESH"

        engine = PyEngine(mesh_analysis)
        engine.run([meshfile, out_dir, out_dir / "mesh_report.html"], cwd=project_root)


__all__ = [
    "ConvergenceStatsJob",
    "FensapConvergenceStatsJob",
    "Drop3dConvergenceStatsJob",
    "Ice3dConvergenceStatsJob",
    "AnalyzeMultishotJob",
    "FensapAnalysisJob",
    "MeshAnalysisJob",
]

