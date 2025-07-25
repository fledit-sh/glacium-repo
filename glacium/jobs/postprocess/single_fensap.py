from __future__ import annotations

from glacium.core.base import PythonJobBase
from glacium.post.convert.single import SingleShotConverter
from glacium.post import PostProcessor, write_manifest


class PostprocessSingleFensapJob(PythonJobBase):
    """Convert FENSAP single-shot results and write manifest."""

    name = "POSTPROCESS_SINGLE_FENSAP"

    def args(self) -> list[str]:
        return []

    def execute(self) -> None:  # noqa: D401
        root = self.project.root
        for dirname in ("run_FENSAP", "run_DROP3D", "run_ICE3D"):
            run_dir = root / dirname
            if run_dir.exists():
                SingleShotConverter(run_dir).convert()
        index = PostProcessor(root).index
        write_manifest(index, root / "manifest.json")
