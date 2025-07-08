import yaml
from pathlib import Path

from glacium.managers.project_manager import ProjectManager


def test_recipe_written(tmp_path):
    pm = ProjectManager(tmp_path)
    airfoil = Path(__file__).resolve().parents[1] / "glacium" / "data" / "AH63K127.dat"

    project = pm.create("proj", "hello", airfoil)
    cfg_file = tmp_path / project.uid / "_cfg" / "global_config.yaml"
    data = yaml.safe_load(cfg_file.read_text())
    assert data["RECIPE"] == "hello"


def test_composite_recipe_saved(tmp_path):
    pm = ProjectManager(tmp_path)
    airfoil = Path(__file__).resolve().parents[1] / "glacium" / "data" / "AH63K127.dat"

    project = pm.create("proj", "prep+solver", airfoil)
    cfg_file = tmp_path / project.uid / "_cfg" / "global_config.yaml"
    data = yaml.safe_load(cfg_file.read_text())
    assert data["RECIPE"] == "prep+solver"
