import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml
import pytest

from glacium.managers.project_manager import ProjectManager
from glacium.managers.template_manager import TemplateManager
from glacium.utils import generate_global_defaults, global_default_config


def test_project_config_generation(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    pm = ProjectManager(tmp_path)
    airfoil = Path(__file__).resolve().parents[1] / "glacium" / "data" / "AH63K127.dat"

    project = pm.create("proj", "prep", airfoil)
    proj_root = tmp_path / project.uid

    case_file = proj_root / "case.yaml"
    cfg_file = proj_root / "_cfg" / "global_config.yaml"

    case = yaml.safe_load(case_file.read_text())
    cfg = yaml.safe_load(cfg_file.read_text())

    expected = generate_global_defaults(case_file, global_default_config())
    assert cfg["FSP_MACH_NUMBER"] == pytest.approx(expected["FSP_MACH_NUMBER"])
    assert cfg["PWS_AIRFOIL_FILE"] == expected["PWS_AIRFOIL_FILE"]
    assert cfg["PWS_REFINEMENT"] == expected["PWS_REFINEMENT"]
