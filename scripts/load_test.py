from pathlib import Path
from typing import Any

from glacium.api import Project
from glacium.utils.logging import log


base_dir = ""
root = Path(base_dir) / "StudyTest"
base = Project.load("StudyTest", "20250802-102115-458416-F3C5")
base.get_grid()

proj = base.clone()
proj.add_job("FENSAP_RUN")
proj.create()
proj.run("FENSAP_RUN")
log.info(f"Finished test sequence {proj.uid} ({proj.root})")