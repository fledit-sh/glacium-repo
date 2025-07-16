"""Base class and registry for pipeline implementations."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Type, Sequence

import yaml

from glacium.utils.JobIndex import JobFactory
from glacium.managers.job_manager import JobManager
from glacium.utils.convergence import project_cl_cd_stats
from glacium.pipelines.step import PipelineStep

from glacium.utils.logging import log
from glacium.managers.project_manager import ProjectManager


class BasePipeline:
    """Base class for all pipelines."""

    name: str = "base"
    description: str = "(no description)"

    def run(self, pm: ProjectManager, steps: Sequence[PipelineStep]):  # noqa: D401
        """Execute ``steps`` using ``pm``.

        Parameters
        ----------
        pm:
            Project manager used to create and load projects.
        steps:
            Ordered list of :class:`PipelineStep` objects describing the
            workflow.

        Returns
        -------
        tuple[list[str], list[tuple[str, float, float, float, float]]]
            Project UIDs and solver statistics for each step.
        """

        default_airfoil = Path(__file__).resolve().parents[1] / "data" / "AH63K127.dat"

        uids: list[str] = []
        stats: list[tuple[str, float, float, float, float]] = []

        for idx, step in enumerate(steps, 1):
            proj_name = f"{self.name}_{idx}"
            project = pm.create(proj_name, step.recipe_name, default_airfoil)
            uids.append(project.uid)

            if step.case_params:
                case_file = project.root / "case.yaml"
                case = yaml.safe_load(case_file.read_text()) or {}
                case.update(step.case_params)
                case_file.write_text(yaml.safe_dump(case, sort_keys=False))

            jm = project.job_manager or JobManager(project)
            jm.run()

            if step.post_jobs:
                for name in step.post_jobs:
                    project.jobs.append(JobFactory.create(name, project))
                project.job_manager = JobManager(project)
                project.job_manager.run(step.post_jobs)

            report_dir = project.root / "run_FENSAP"
            if report_dir.exists():
                stats.append((project.uid, *project_cl_cd_stats(report_dir)))

        return uids, stats

    # ------------------------------------------------------------------
    def merge_pdfs(
        self,
        pm: ProjectManager,
        uids: Sequence[str],
        stats: Sequence[tuple[str, float, float, float, float]],
        out_file: Path | None = None,
    ) -> Path:
        """Merge per-project analysis reports with a summary.

        Parameters
        ----------
        pm:
            Project manager that created the projects.
        uids:
            Sequence of project UIDs in the order they were executed.
        stats:
            Statistics returned by :meth:`run` for each project.
        out_file:
            Output file.  Defaults to ``pm.runs_root.parent /
            f"{pm.runs_root.name}_summary.pdf"``.

        Returns
        -------
        Path
            The path of the merged PDF.
        """

        from tempfile import NamedTemporaryFile

        from fpdf import FPDF
        from PyPDF2 import PdfMerger

        if out_file is None:
            out_file = pm.runs_root.parent / f"{pm.runs_root.name}_summary.pdf"

        # ------------------------------------------------------------------
        # Build summary page -------------------------------------------------
        pdf = FPDF(format="A4")
        pdf.set_auto_page_break(True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", size=14)
        pdf.cell(0, 10, "Pipeline Summary", ln=True, align="C")
        pdf.ln(4)

        widths = (45, 30, 30, 30, 30)
        headers = ("UID", "CL mean", "CL std", "CD mean", "CD std")
        pdf.set_font("Helvetica", size=10)
        pdf.set_fill_color(200, 200, 200)
        for w, h in zip(widths, headers):
            pdf.cell(w, 6, h, border=1, align="C", fill=True)
        pdf.ln()
        pdf.set_fill_color(255, 255, 255)
        for uid, cl_mean, cl_std, cd_mean, cd_std in stats:
            pdf.cell(widths[0], 6, uid, border=1)
            pdf.cell(widths[1], 6, f"{cl_mean:.3f}", border=1, align="R")
            pdf.cell(widths[2], 6, f"{cl_std:.3f}", border=1, align="R")
            pdf.cell(widths[3], 6, f"{cd_mean:.3f}", border=1, align="R")
            pdf.cell(widths[4], 6, f"{cd_std:.3f}", border=1, align="R")
            pdf.ln()

        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            summary_path = Path(tmp.name)

        # ------------------------------------------------------------------
        # Merge all PDFs ----------------------------------------------------
        merger = PdfMerger()
        merger.append(str(summary_path))

        for uid in uids:
            base = pm.runs_root / uid / "analysis"
            for sub in ("MULTISHOT", "FENSAP", "DROP3D", "ICE3D", ""):
                pdf_path = base / sub / "report.pdf" if sub else base / "report.pdf"
                if pdf_path.exists():
                    merger.append(str(pdf_path))
                    break

        out_file.parent.mkdir(parents=True, exist_ok=True)
        with out_file.open("wb") as fh:
            merger.write(fh)
        merger.close()

        summary_path.unlink(missing_ok=True)
        log.success(f"Merged PDF written → {out_file}")

        return out_file


class PipelineManager:
    _pipelines: Dict[str, Type[BasePipeline]] | None = None

    @classmethod
    def create(cls, name: str) -> BasePipeline:
        """Instantiate the pipeline registered as ``name``."""

        cls._load()
        if name not in cls._pipelines:  # type: ignore[arg-type]
            raise KeyError(f"Pipeline '{name}' nicht registriert.")
        return cls._pipelines[name]()  # type: ignore[index]

    @classmethod
    def list(cls) -> List[str]:
        """Return the names of all registered pipelines."""

        cls._load()
        return sorted(cls._pipelines)  # type: ignore[arg-type]

    @classmethod
    def register(cls, pipe_cls: Type[BasePipeline]):
        """Class decorator to register ``pipe_cls``."""

        cls._load()
        if pipe_cls.name in cls._pipelines:  # type: ignore
            log.warning(f"Pipeline '{pipe_cls.name}' wird überschrieben.")
        cls._pipelines[pipe_cls.name] = pipe_cls  # type: ignore[index]
        return pipe_cls

    # Internal -------------------------------------------------------------
    @classmethod
    def _load(cls):
        """Populate the internal pipeline registry if empty."""

        if cls._pipelines is not None:
            return
        cls._pipelines = {}
        cls._discover("glacium.pipelines")
        log.debug(f"Pipelines: {', '.join(cls._pipelines)}")  # type: ignore[arg-type]

    @classmethod
    def _discover(cls, pkg_name: str):
        """Import all submodules from ``pkg_name`` to populate registry."""

        try:
            pkg = importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            return
        pkg_path = Path(pkg.__file__).parent
        for mod in pkgutil.iter_modules([str(pkg_path)]):
            importlib.import_module(f"{pkg_name}.{mod.name}")
