import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.managers.project_manager import ProjectManager
from glacium.managers.template_manager import TemplateManager


def test_project_create_prepares_jobs(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    pm = ProjectManager(tmp_path)
    airfoil = Path(__file__).resolve().parents[1] / "glacium" / "data" / "AH63K127.dat"
    project = pm.create("proj", "prep", airfoil)
    script = tmp_path / project.uid / "xfoil" / "XFOIL.increasepoints.in"
    assert script.exists()
