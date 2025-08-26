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

    # fake minimal glacium.post.multishot.plot_s module
    plot_s_mod = types.ModuleType("plot_s")
    plot_s_mod._read_first_zone_with_conn = lambda path: None
    glacium_pkg = types.ModuleType("glacium")
    glacium_pkg.__path__ = []
    post_pkg = types.ModuleType("glacium.post")
    post_pkg.__path__ = []
    multishot_pkg = types.ModuleType("glacium.post.multishot")
    multishot_pkg.__path__ = []
    monkeypatch.setitem(sys.modules, "glacium", glacium_pkg)
    monkeypatch.setitem(sys.modules, "glacium.post", post_pkg)
    monkeypatch.setitem(sys.modules, "glacium.post.multishot", multishot_pkg)
    monkeypatch.setitem(sys.modules, "glacium.post.multishot.plot_s", plot_s_mod)

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


def test_wall_min_xc_used_over_slice(monkeypatch, tmp_path):
    pv_stub = types.SimpleNamespace(
        Plotter=type("Plotter", (), {}),
        Camera=type("Camera", (), {}),
        MultiBlock=type("MultiBlock", (), {}),
        global_theme=types.SimpleNamespace(show_scalar_bar=False),
    )
    # simple grid and slice with min x = 0.0
    pts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    slc = types.SimpleNamespace(points=pts, bounds=(0, 0, -1, 1, 0, 0))
    grid = types.SimpleNamespace(points=pts.copy(), slice=lambda normal: slc)

    class Reader:
        def __init__(self, path):
            pass

        def read(self):
            return grid

    pv_stub.TecplotReader = Reader
    monkeypatch.setitem(sys.modules, "pyvista", pv_stub)
    monkeypatch.setitem(sys.modules, "scienceplots", types.ModuleType("scienceplots"))

    # fake minimal glacium.post.multishot.plot_s module
    nodes = np.array([[-0.3, 0.0, 0.0], [0.2, 0.0, 0.0]])

    def fake_read(path):
        return nodes, np.empty((0, 2), int), ["X", "Y", "Z"], {"x": 0}

    plot_s_mod = types.ModuleType("plot_s")
    plot_s_mod._read_first_zone_with_conn = fake_read
    glacium_pkg = types.ModuleType("glacium")
    glacium_pkg.__path__ = []
    post_pkg = types.ModuleType("glacium.post")
    post_pkg.__path__ = []
    multishot_pkg = types.ModuleType("glacium.post.multishot")
    multishot_pkg.__path__ = []
    monkeypatch.setitem(sys.modules, "glacium", glacium_pkg)
    monkeypatch.setitem(sys.modules, "glacium.post", post_pkg)
    monkeypatch.setitem(sys.modules, "glacium.post.multishot", multishot_pkg)
    monkeypatch.setitem(sys.modules, "glacium.post.multishot.plot_s", plot_s_mod)

    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import style as mpl_style
    monkeypatch.setattr(mpl_style, "use", lambda *args, **kwargs: None)

    module_path = Path(__file__).resolve().parents[1] / "glacium" / "post" / "analysis" / "fensap_flow_plots.py"
    spec = importlib.util.spec_from_file_location("fensap_flow_plots", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(module, "ensure_outdir", lambda d: d)

    captured = {}

    class StopCalled(Exception):
        pass

    def fake_build_views(min_xc):
        captured["min"] = min_xc
        raise StopCalled

    monkeypatch.setattr(module, "build_views", fake_build_views)

    dummy = tmp_path / "dummy.dat"
    dummy.write_text("dummy")
    with pytest.raises(StopCalled):
        module.main([str(dummy), str(tmp_path)])

    assert captured["min"] == -0.3
