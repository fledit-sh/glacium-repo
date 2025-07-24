from __future__ import annotations

from glacium.models.job import Job
from glacium.post.convert.single import SingleShotConverter
from glacium.post import PostProcessor, write_manifest


class PostprocessSingleFensapJob(Job):
    """Convert FENSAP single-shot results and write manifest."""

    name = "POSTPROCESS_SINGLE_FENSAP"

    def execute(self) -> None:  # noqa: D401
        root = self.project.root
        for dirname in ("run_FENSAP", "run_DROP3D", "run_ICE3D"):
            run_dir = root / dirname
            if run_dir.exists():
                SingleShotConverter(run_dir).convert()
        index = PostProcessor(root).index
        write_manifest(index, root / "manifest.json")
