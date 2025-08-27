import importlib
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _prepare_import():
    import matplotlib.pyplot as plt

    # Prevent style lookups during import and provide missing scienceplots
    plt.style.use = lambda *args, **kwargs: None
    sys.modules.setdefault("scienceplots", types.ModuleType("scienceplots"))

    # Provide minimal glacium package structure to satisfy imports
    pkg = types.ModuleType("glacium")
    api_pkg = types.ModuleType("glacium.api")
    managers_pkg = types.ModuleType("glacium.managers")
    pm_pkg = types.ModuleType("glacium.managers.project_manager")
    utils_pkg = types.ModuleType("glacium.utils")
    conv_pkg = types.ModuleType("glacium.utils.convergence")
    logging_pkg = types.ModuleType("glacium.utils.logging")

    class _Project:
        pass

    class _PM:
        def __init__(self, *args, **kwargs):
            pass

    api_pkg.Project = _Project
    pm_pkg.ProjectManager = _PM
    managers_pkg.project_manager = pm_pkg
    conv_pkg.project_cl_cd_stats = lambda *a, **k: (float("nan"),) * 4
    logging_pkg.log = types.SimpleNamespace(error=lambda *a, **k: None)

    sys.modules.update(
        {
            "glacium": pkg,
            "glacium.api": api_pkg,
            "glacium.managers": managers_pkg,
            "glacium.managers.project_manager": pm_pkg,
            "glacium.utils": utils_pkg,
            "glacium.utils.convergence": conv_pkg,
            "glacium.utils.logging": logging_pkg,
        }
    )


def test_clean_analysis_injects_aoa0(monkeypatch, tmp_path):
    _prepare_import()
    mod = importlib.import_module("scripts.09_clean_sweep_analysis")

    sweep_runs = [(2.0, 2.0, 0.2, object())]
    aoa0_runs = [(0.0, 0.1, 0.01, object())]

    def fake_load_runs(root, exclude_zero=False):
        root = Path(root)
        if root.name == "08_clean_sweep":
            return list(sweep_runs)
        return list(aoa0_runs)

    captured = {}

    def fake_analysis(runs, out_dir):
        captured["runs"] = list(runs)

    monkeypatch.setattr(mod, "load_runs", fake_load_runs)
    monkeypatch.setattr(mod, "aoa_sweep_analysis", fake_analysis)

    mod.main(tmp_path)

    assert captured["runs"][0][:3] == sweep_runs[0][:3]
    assert captured["runs"][-1][:3] == (0.0, aoa0_runs[0][1], aoa0_runs[0][2])


def test_iced_analysis_injects_aoa0(monkeypatch, tmp_path):
    _prepare_import()
    mod = importlib.import_module("scripts.11_iced_sweep_analysis")

    sweep_runs = [(3.0, 3.0, 0.3, object())]
    aoa0_runs = [(0.0, 0.2, 0.02, object())]

    def fake_load_runs(root, exclude_zero=False):
        root = Path(root)
        if root.name == "10_iced_sweep":
            return list(sweep_runs)
        return list(aoa0_runs)

    captured = {}

    def fake_analysis(runs, out_dir):
        captured["runs"] = list(runs)

    monkeypatch.setattr(mod, "load_runs", fake_load_runs)
    monkeypatch.setattr(mod, "aoa_sweep_analysis", fake_analysis)

    mod.main(tmp_path)

    assert captured["runs"][0][:3] == sweep_runs[0][:3]
    assert captured["runs"][-1][:3] == (0.0, aoa0_runs[0][1], aoa0_runs[0][2])

