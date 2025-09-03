from pathlib import Path
import sys
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# stub heavy optional dependencies before importing glacium modules
for mod in ["pandas", "scienceplots"]:
    sys.modules.setdefault(mod, types.ModuleType(mod))

pv_stub = types.SimpleNamespace(
    Plotter=type("Plotter", (), {}),
    Camera=type("Camera", (), {}),
    MultiBlock=type("MultiBlock", (), {}),
    TecplotReader=type("TecplotReader", (), {}),
    global_theme=types.SimpleNamespace(show_scalar_bar=False),
)
sys.modules.setdefault("pyvista", pv_stub)

ruamel = types.ModuleType("ruamel")
class DummyYAML:
    def __init__(self, *args, **kwargs):
        pass
    def indent(self, *args, **kwargs):
        pass
    def load(self, *args, **kwargs):
        return {}
    def dump(self, *args, **kwargs):
        pass

ruamel_yaml = types.SimpleNamespace(YAML=DummyYAML)
ruamel.yaml = ruamel_yaml
sys.modules.setdefault("ruamel", ruamel)
sys.modules.setdefault("ruamel.yaml", ruamel_yaml)

import matplotlib
matplotlib.use("Agg")
from matplotlib import style as mpl_style
mpl_style.use = lambda *args, **kwargs: None

from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project


def test_mesh_visualization_job(monkeypatch, tmp_path):
    pv_stub = types.SimpleNamespace(
        Plotter=type("Plotter", (), {}),
        Camera=type("Camera", (), {}),
        MultiBlock=type("MultiBlock", (), {}),
        TecplotReader=type("TecplotReader", (), {}),
        global_theme=types.SimpleNamespace(show_scalar_bar=False),
    )
    monkeypatch.setitem(sys.modules, "pyvista", pv_stub)
    monkeypatch.setitem(sys.modules, "scienceplots", types.ModuleType("scienceplots"))

    from glacium.jobs.analysis_jobs import MeshVisualizationJob
    import glacium.jobs.analysis_jobs as analysis_jobs

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path, FSP_CHARAC_LENGTH=1.5)
    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    mesh_dir = tmp_path / "mesh"
    mesh_dir.mkdir(exist_ok=True)
    mesh_file = mesh_dir / "mesh.cas"
    mesh_file.write_text("")

    project = Project("uid", tmp_path, cfg, paths, [])
    job = MeshVisualizationJob(project)
    job.deps = ()
    project.jobs = [job]

    called = {}

    def fake_fensap_mesh_plots(cwd, args):
        called["cwd"] = cwd
        called["args"] = list(args)

    monkeypatch.setattr(analysis_jobs, "fensap_mesh_plots", fake_fensap_mesh_plots)

    job.execute()

    out_dir = tmp_path / "analysis" / "MESH"
    assert called["cwd"] == tmp_path
    assert called["args"] == [str(mesh_file), "--scale", "1.5", "-o", str(out_dir)]
