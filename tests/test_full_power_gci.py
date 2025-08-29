import sys
from pathlib import Path
import yaml
import math
import pytest
from importlib.machinery import SourceFileLoader
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.managers.project_manager import ProjectManager
from glacium.managers.template_manager import TemplateManager

module_path = Path(__file__).resolve().parents[1] / "scripts" / "02_full_power_gci.py"
full_power_gci = SourceFileLoader("full_power_gci", str(module_path)).load_module()
load_runs = full_power_gci.load_runs
gci_analysis2 = full_power_gci.gci_analysis2
compute_h_from_merged = full_power_gci.compute_h_from_merged


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

    # minimal merged.dat for h computation
    merged = project.root / "analysis" / "FENSAP" / "merged.dat"
    merged.parent.mkdir(parents=True, exist_ok=True)
    merged.write_text(
        (
            'TITLE="t"\n'
            'VARIABLES="X","Y"\n'
            'ZONE T="L1", N=2, E=1, ZONETYPE=FELINESEG, DATAPACKING=POINT\n'
            '0 0\n'
            '1 0\n'
            '1 2\n'
        )
    )
    soln = project.root / "run_FENSAP" / "soln.dat"
    soln.parent.mkdir(parents=True, exist_ok=True)
    soln.write_text("dummy")
    expected_h = compute_h_from_merged(merged)

    runs = load_runs(tmp_path)
    assert len(runs) == 1
    h, cl, cd, proj = runs[0]

    assert not math.isnan(h)
    assert not math.isnan(cl)
    assert not math.isnan(cd)

    assert h == pytest.approx(expected_h)
    assert cl == pytest.approx(results["LIFT_COEFFICIENT"])
    assert cd == pytest.approx(results["DRAG_COEFFICIENT"])
    assert proj.uid == project.uid


def test_load_runs_skips_missing_soln(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    pm = ProjectManager(tmp_path)
    airfoil = Path(__file__).resolve().parents[1] / "glacium" / "data" / "AH63K127.dat"
    pm.create("proj", "hello", airfoil)

    runs = load_runs(tmp_path)
    assert runs == []


def test_best_triplet_selected_from_cl(tmp_path, monkeypatch):
    """gci_analysis2 should pick the triplet with lowest E(CL)."""
    h_vals = [1.0, 2.0, 4.0, 8.0]
    cl_vals = [1.0, 0.95, 0.88, 0.8]
    cd_vals = [0.3, 0.28, 0.25, 0.19]

    runs = []
    for i, (h, cl, cd) in enumerate(zip(h_vals, cl_vals, cd_vals)):
        proj_root = tmp_path / f"p{i}"
        log_file = proj_root / "run_FENSAP" / ".solvercmd.out"
        log_file.parent.mkdir(parents=True)
        log_file.write_text("total simulation = 0:00:01\n")
        runs.append((h, cl, cd, SimpleNamespace(root=proj_root, uid=f"p{i}")))
        assert log_file.exists()

    captured = {}

    def fake_report(**kwargs):
        captured["run_table"] = kwargs.get("run_table")

    monkeypatch.setattr(full_power_gci, "generate_gci_pdf_report", fake_report)

    scatter_calls: list = []
    legend_calls: list = []
    monkeypatch.setattr(full_power_gci.plt, "scatter", lambda *a, **k: scatter_calls.append((a, k)))
    monkeypatch.setattr(full_power_gci.plt, "legend", lambda *a, **k: legend_calls.append((a, k)))

    best, results, best_proj = gci_analysis2(runs, tmp_path)

    assert scatter_calls == []
    assert legend_calls == []

    for _, _, _, proj in runs:
        assert (proj.root / "run_FENSAP" / ".solvercmd.out").exists()

    assert best[0] == pytest.approx(h_vals[0])
    assert best_proj.uid == "p0"

    expected = [
        (f"p{i}", h, cl, cd) for i, (h, cl, cd) in enumerate(zip(h_vals, cl_vals, cd_vals))
    ]
    assert captured["run_table"] == expected


def test_compute_h_from_merged(tmp_path):
    merged = tmp_path / "merged.dat"
    merged.write_text(
        (
            'TITLE="t"\n'
            'VARIABLES="X","Y"\n'
            'ZONE T="L1", N=2, E=1, ZONETYPE=FELINESEG, DATAPACKING=POINT\n'
            '0 0\n'
            '1 0\n'
            '1 2\n'
        )
    )
    h = compute_h_from_merged(merged)
    assert h == pytest.approx(0.5)
