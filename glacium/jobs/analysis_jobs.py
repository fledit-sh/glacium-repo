"""Job classes performing post-processing analysis."""

from glacium.models.job import Job
from glacium.engines.py_engine import PyEngine
from glacium.utils.convergence import analysis, analysis_file
from glacium.utils.report_converg_fensap import build_report


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


__all__ = [
    "ConvergenceStatsJob",
    "FensapConvergenceStatsJob",
    "Drop3dConvergenceStatsJob",
    "Ice3dConvergenceStatsJob",
]

