"""Dataclasses representing a Glacium project on disk."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathManager
from glacium.models.job import Job
# JobManager wird dynamisch gesetzt, daher nur Typ-Import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass


@dataclass
class Project:
    """Container holding configuration, jobs and paths for a project."""

    uid: str
    root: Path
    config: GlobalConfig
    paths: PathManager
    jobs: List[Job] = field(default_factory=list)
    # Wird nachträglich vom ``ProjectManager`` gesetzt
    job_manager: "JobManager | None" = None

