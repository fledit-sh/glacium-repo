"""Post-processing job classes."""

from __future__ import annotations

from pathlib import Path

from glacium.models.job import Job
from glacium.post.convert.single import SingleShotConverter
from glacium.post.convert.multishot import MultiShotConverter
from glacium.post import PostProcessor, write_manifest

__all__ = ["PostprocessSingleFensapJob", "PostprocessMultishotJob"]


class PostprocessSingleFensapJob(Job):
    """Convert FENSAP single-shot results and write manifest."""

    name = "POSTPROCESS_SINGLE_FENSAP"
    deps = ("FENSAP_RUN", "DROP3D_RUN", "ICE3D_RUN")

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
        ms_dir = root / "analysis" / "run_MULTISHOT"
        index = MultiShotConverter(ms_dir).convert_all()
        write_manifest(index, root / "manifest.json")

