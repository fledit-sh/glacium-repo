"""Utility helpers for listing projects on disk."""

from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class ProjectInfo:
    """Information collected from a project folder."""

    uid: str
    name: str  # optional
    jobs_done: int
    jobs_total: int
    path: Path

def list_projects(root: Path) -> list[ProjectInfo]:
    """Return a sorted list of :class:`ProjectInfo` objects found below ``root``."""

    items: list[ProjectInfo] = []
    for p in root.iterdir():
        if not p.is_dir():
            continue
        cfg_file = p / "global_config.yaml"
        if not cfg_file.exists():
            cfg_file = p / "_cfg" / "global_config.yaml"
        jobs_file = p / "_cfg" / "jobs.yaml"
        name = "(unnamed)"
        done, total = 0, 0

        if cfg_file.exists():
            cfg = yaml.safe_load(cfg_file.read_text()) or {}
            name = cfg.get("PROJECT_NAME", name)

        if jobs_file.exists():
            data = yaml.safe_load(jobs_file.read_text()) or {}
            total = len(data)
            done = sum(1 for s in data.values() if s == "DONE")

        items.append(ProjectInfo(p.name, name, done, total, p))
    return sorted(items, key=lambda x: x.uid, reverse=True)

