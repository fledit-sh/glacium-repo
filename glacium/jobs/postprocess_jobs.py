"""Post-processing job classes."""

from __future__ import annotations

from pathlib import Path

from glacium.models.job import Job
from glacium.post.convert.single import SingleShotConverter
from glacium.post.convert.multishot import MultiShotConverter
from glacium.post import PostProcessor, write_manifest

__all__ = ["PostprocessSingleFensapJob", "PostprocessMultishotJob"]


class PostprocessSingleFensapJob(Job):
    """Convert FENSAP single-shot results and write manifest.

    The dependency list is determined at runtime based on which solver
    runs exist in ``project.jobs``.  ``FENSAP_RUN`` is always required
    while ``DROP3D_RUN`` and ``ICE3D_RUN`` are added only if present.
    """

    name = "POSTPROCESS_SINGLE_FENSAP"
    deps = ("FENSAP_RUN",)  # further dependencies resolved dynamically

    def __init__(self, project):
        super().__init__(project)
        job_names = {j.name for j in project.jobs}
        deps = ["FENSAP_RUN"]
        if "DROP3D_RUN" in job_names:
            deps.append("DROP3D_RUN")
        if "ICE3D_RUN" in job_names:
            deps.append("ICE3D_RUN")
        self.deps = tuple(deps)

    def execute(self) -> None:  # noqa: D401
        root = self.project.root
        for dirname in ("run_FENSAP", "run_DROP3D", "run_ICE3D"):
            run_dir = root / dirname
            if run_dir.exists():
                SingleShotConverter(run_dir).convert()
        index = PostProcessor(root).index
        write_manifest(index, root / "manifest.json")


class PostprocessMultishotJob(Job):
    """Convert MULTISHOT results and write manifest."""

    name = "POSTPROCESS_MULTISHOT"
    deps = ("MULTISHOT_RUN",)

    def execute(self) -> None:  # noqa: D401
        root = self.project.root
        ms_dir = root / "run_MULTISHOT"
        index = MultiShotConverter(ms_dir).convert_all()
        write_manifest(index, root / "manifest.json")

