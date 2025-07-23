import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from glacium.api import Project
from glacium.managers.template_manager import TemplateManager


def test_project_get(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    proj = Project(tmp_path).set("CASE_VELOCITY", 42).set("FSP_MAX_TIME_STEPS_PER_CYCLE", 7).create()

    assert proj.get("case_velocity") == 42
    assert proj.get("fsp_max_time_steps_per_cycle") == 7

    with pytest.raises(KeyError):
        proj.get("unknown_key")


def test_project_get_results(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    proj = Project(tmp_path).create()

    (proj.root / "results.yaml").write_text("CL_MEAN: 2.5\n")

    assert proj.get("cl_mean") == 2.5
