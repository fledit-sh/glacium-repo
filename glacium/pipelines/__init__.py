from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence, Any
from ..managers.project_manager import ProjectManager
from ..managers.job_manager import JobManager
from ..api.run import Run

class PipelineManager:
    def __init__(self, layout: str) -> None:
        self.layout = layout

    @classmethod
    def create(cls, layout: str) -> "PipelineManager":
        return cls(layout)

    def run(
        self,
        pm: ProjectManager,
        *,
        levels: Sequence[int],
        params: dict[str, Any] | None = None,
        multishots: Sequence[Sequence[int]] = (),
    ) -> tuple[list[str], list[int]]:
        params = params or {}
        uids: list[str] = []
        stats: list[int] = []
        best_level = levels[0] if levels else 1
        # grid studies ---------------------------------------------------
        for lvl in levels:
            run = Run(pm.runs_root).set("PWS_REFINEMENT", lvl)
            for k, v in params.items():
                run.set(k, v)
            project = run.create()
            JobManager(project).run()
            uids.append(project.uid)
            stats.append(lvl)
            best_level = levels[0]
        # single shot ----------------------------------------------------
        run = Run(pm.runs_root).set("PWS_REFINEMENT", best_level)
        project = run.create()
        JobManager(project).run()
        uids.append(project.uid)
        stats.append(best_level)
        # multishot sequences -------------------------------------------
        for seq in multishots:
            r = (
                Run(pm.runs_root)
                .set("RECIPE", "multishot")
                .set("PWS_REFINEMENT", best_level)
                .set("CASE_MULTISHOT", list(seq))
            )
            project = r.create()
            JobManager(project).run()
            uids.append(project.uid)
            stats.append(best_level)
        return uids, stats

    def merge_pdfs(self, pm: ProjectManager, uids: Sequence[str], stats: Iterable[Any]):
        from PyPDF2 import PdfMerger
        out = pm.runs_root.parent / "runs_summary.pdf"
        merger = PdfMerger()
        for uid in uids:
            base = pm.runs_root / uid / "analysis"
            for solver in ["MULTISHOT", "FENSAP"]:
                pdf = base / solver / "report.pdf"
                if pdf.exists():
                    merger.append(str(pdf))
        merger.write(str(out))
        merger.close()
        return out

__all__ = ["PipelineManager"]
