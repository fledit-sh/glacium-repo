from __future__ import annotations

from pathlib import Path
import yaml

from glacium.api import ProjectBuilder
from glacium.managers.project_manager import ProjectManager
from glacium.utils import generate_global_defaults, global_default_config


class ProjectService:
    """High level project operations used by the CLI."""

    def __init__(self, root: Path = Path("runs")) -> None:
        self.root = root

    def create_project(
        self,
        name: str,
        recipe: str,
        airfoil: Path,
        *,
        multishots: int | None = None,
    ):
        builder = ProjectBuilder(self.root)
        builder.name(name).select_airfoil(airfoil)
        builder.set("recipe", recipe)
        if multishots is not None:
            builder.set("multishot_count", multishots)
        return builder.create()

    def update_config(self, uid: str, case_file: Path | None = None) -> Path:
        pm = ProjectManager(self.root)
        proj = pm.load(uid)
        src = case_file or (proj.root / "case.yaml")
        cfg = generate_global_defaults(src, global_default_config())
        dest = proj.paths.global_cfg_file()
        existing = yaml.safe_load(dest.read_text()) if dest.exists() else {}
        merged = dict(existing)
        merged.update(cfg)
        dest.write_text(yaml.safe_dump(merged, sort_keys=False))
        return dest
