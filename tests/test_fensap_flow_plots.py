import types
import sys
import importlib
import importlib.util
from pathlib import Path
import numpy as np
import pytest


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
        if np.isclose(base_xmin, -0.1):
            assert new_xmin == min_xc
        else:
            assert new_xmin == base_xmin


def test_main_calls_build_views_for_all_values(monkeypatch, tmp_path):
    pv_stub = types.SimpleNamespace(
        Plotter=type("Plotter", (), {}),
        Camera=type("Camera", (), {}),
        MultiBlock=type("MultiBlock", (), {}),
        global_theme=types.SimpleNamespace(show_scalar_bar=False),
    )

    pts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    slc = types.SimpleNamespace(
        points=pts,
        point_data={"foo": np.array([0.0, 1.0])},
        bounds=(0, 1, -1, 1, 0, 0),
    )
    grid = types.SimpleNamespace(points=pts.copy(), slice=lambda normal: slc)

    class Reader:
        def __init__(self, path):
            pass

        def read(self):
            return grid

    pv_stub.TecplotReader = Reader
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

    dummy_png = tmp_path / "dummy.png"
    dummy_png.write_text("dummy")

    calls = []

    def fake_build_views(base):
        calls.append(base)
        return [((0, 1), 0.0, "overview")]

    monkeypatch.setattr(module, "build_views", fake_build_views)
    monkeypatch.setattr(
        module,
        "pyvista_render_and_shoot",
        lambda *args, **kwargs: ((0, 1), (0, 1), (0, 1), dummy_png, "plasma"),
    )
    monkeypatch.setattr(module, "overlay_axes_on_screenshot", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "ensure_outdir", lambda d: d)

    dummy = tmp_path / "dummy.dat"
    dummy.write_text("dummy")
    module.main([str(dummy), str(tmp_path)])

    assert calls == module.MIN_XC_VALUES
