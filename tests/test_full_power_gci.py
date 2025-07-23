import sys
from pathlib import Path
import yaml
import math
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.managers.project_manager import ProjectManager
from glacium.managers.template_manager import TemplateManager
from scripts.full_power_gci import load_runs


def test_load_runs_reads_results(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    pm = ProjectManager(tmp_path)
    airfoil = Path(__file__).resolve().parents[1] / "glacium" / "data" / "AH63K127.dat"
    project = pm.create("proj", "hello", airfoil)

    # write CL and CD into results.yaml
    results = {"LIFT_COEFFICIENT": 1.23, "DRAG_COEFFICIENT": 0.045}
    (project.root / "results.yaml").write_text(yaml.safe_dump(results, sort_keys=False))

    cfg_file = project.root / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    assert "PWS_REFINEMENT" in cfg

    runs = load_runs(tmp_path)
    assert len(runs) == 1
    refinement, cl, cd, proj = runs[0]

    assert not math.isnan(refinement)
    assert not math.isnan(cl)
    assert not math.isnan(cd)

    assert refinement == pytest.approx(float(cfg["PWS_REFINEMENT"]))
    assert cl == pytest.approx(results["LIFT_COEFFICIENT"])
    assert cd == pytest.approx(results["DRAG_COEFFICIENT"])
    assert proj.uid == project.uid
