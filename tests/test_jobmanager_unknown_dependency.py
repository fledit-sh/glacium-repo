import sys
import types
from pathlib import Path

import pytest


# Avoid executing glacium.__init__ (pulls heavy optional deps)
pkg_root = Path(__file__).resolve().parents[1] / "glacium"
glacium_stub = types.ModuleType("glacium")
glacium_stub.__path__ = [str(pkg_root)]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.modules.setdefault("glacium", glacium_stub)

from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project
from glacium.managers.job_manager import JobManager
from glacium.models.job import Job


def _project(root: Path) -> Project:
    cfg = GlobalConfig(project_uid="uid", base_dir=root)
    paths = PathBuilder(root).build()
    paths.ensure()
    return Project("uid", root, cfg, paths, [])


def test_missing_dependency_raises(tmp_path):
    project = _project(tmp_path)

    class A(Job):
        name = "A"
        deps = ("B",)

        def execute(self):
            pass

    project.jobs = [A(project)]

    jm = JobManager(project)
    with pytest.raises(RuntimeError):
        jm.run()

