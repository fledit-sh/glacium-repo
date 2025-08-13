import sys
from pathlib import Path
import yaml
import math
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.managers.project_manager import ProjectManager
from glacium.managers.template_manager import TemplateManager
import importlib

full_power_gci = importlib.import_module("scripts.02_full_power_gci")
load_runs = full_power_gci.load_runs
gci_analysis2 = full_power_gci.gci_analysis2
from types import SimpleNamespace


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


def test_best_triplet_selected_from_cl(tmp_path):
    """gci_analysis2 should pick the triplet with lowest E(CL)."""
    factors = [1.0, 2.0, 4.0, 8.0]
    cl_vals = [1.0, 0.95, 0.88, 0.8]
    cd_vals = [0.3, 0.28, 0.25, 0.19]

    runs = []
    for i, (f, cl, cd) in enumerate(zip(factors, cl_vals, cd_vals)):
        proj_root = tmp_path / f"p{i}"
        log_file = proj_root / "run_FENSAP" / ".solvercmd.out"
        log_file.parent.mkdir(parents=True)
        log_file.write_text("total simulation = 0:00:01\n")
        runs.append((f, cl, cd, SimpleNamespace(root=proj_root, uid=f"p{i}")))

    best, results, best_proj = gci_analysis2(runs, tmp_path)

    assert best[0] == pytest.approx(factors[0])
    assert best_proj.uid == "p0"
