from __future__ import annotations

from glacium.core.base import PythonJobBase
from glacium.post.convert.multishot import MultiShotConverter
from glacium.post import write_manifest


class PostprocessMultishotJob(PythonJobBase):
    """Convert MULTISHOT results and write manifest."""

    name = "POSTPROCESS_MULTISHOT"

    def args(self) -> list[str]:
        return []

    def execute(self) -> None:  # noqa: D401
        root = self.project.root
        ms_dir = root / "run_MULTISHOT"
        index = MultiShotConverter(ms_dir).convert_all()
        write_manifest(index, root / "manifest.json")
