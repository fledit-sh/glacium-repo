# glacium/models/project.py
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from glacium.models.config import GlobalConfig
from glacium.managers.PathManager import PathManager
from glacium.models.job import Job
# JobManager wird dynamisch gesetzt, daher nur Typ-Import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass


@dataclass
class Project:
    uid: str
    root: Path
    config: GlobalConfig
    paths: PathManager
    jobs: List[Job] = field(default_factory=list)
    # wird nachträglich vom ProjectManager gesetzt
    job_manager: "JobManager | None" = None
