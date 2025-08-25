import types
import sys
import importlib
import importlib.util
from pathlib import Path
import numpy as np


def test_views_adjust_minimum(monkeypatch):
    pv_stub = types.SimpleNamespace(
        Plotter=type("Plotter", (), {}),
        Camera=type("Camera", (), {}),
        MultiBlock=type("MultiBlock", (), {}),
        TecplotReader=type("TecplotReader", (), {}),
        global_theme=types.SimpleNamespace(show_scalar_bar=False),
    )
    monkeypatch.setitem(sys.modules, "pyvista", pv_stub)
    monkeypatch.setitem(sys.modules, "scienceplots", types.ModuleType("scienceplots"))

    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import style as mpl_style
    monkeypatch.setattr(mpl_style, "use", lambda *args, **kwargs: None)

    module_path = Path(__file__).resolve().parents[1] / "glacium" / "post" / "analysis" / "fensap_flow_plots.py"
    spec = importlib.util.spec_from_file_location("fensap_flow_plots", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    pts = np.array([[-0.5, 0.0, 0.0], [0.0, 1.0, 0.0], [0.8, -1.0, 0.0]])
    slc = types.SimpleNamespace(points=pts)
    min_xc = float(np.min(slc.points[:, 0]))

    views = module.build_views(min_xc)

    for base, view in zip(module.BASE_VIEWS, views):
        base_xmin = base[0][0]
        new_xmin = view[0][0]
        if np.isclose(base_xmin, -0.2):
            assert new_xmin == min_xc
        else:
            assert new_xmin == base_xmin
