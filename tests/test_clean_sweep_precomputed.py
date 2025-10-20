import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import Mock


def _load_script(monkeypatch, filename: str, module_name: str):
    """Load a script module with stubbed glacium dependencies."""
    # create minimal package structure for glacium
    glacium_pkg = types.ModuleType("glacium")
    glacium_pkg.__path__ = []
    utils_pkg = types.ModuleType("glacium.utils")
    utils_pkg.__path__ = []
    logging_pkg = types.ModuleType("glacium.utils.logging")
    logging_pkg.log = type("Log", (), {"error": lambda *a, **k: None})()
    utils_pkg.logging = logging_pkg
    managers_pkg = types.ModuleType("glacium.managers")
    managers_pkg.__path__ = []
    pm_pkg = types.ModuleType("glacium.managers.project_manager")
    cfg_pkg = types.ModuleType("glacium.managers.config_manager")
    cfg_pkg.ConfigManager = type("ConfigManager", (), {})
    multishot_mod = types.ModuleType("multishot_loader")

    # placeholder functions/classes
    class Project:
        def __init__(self, root):
            self.root = root
            self.uid = "uid"

        def name(self, _name: str):
            return self

        def set_bulk(self, _params):
            return self

        def set(self, key, value):
            pass

        def add_job(self, job):
            pass

        def create(self):
            return self

        def clone(self):
            return self

        def run(self):
            pass

        @classmethod
        def load(cls, *a, **k):  # placeholder patched in tests
            return None

    pm_pkg.ProjectManager = type("ProjectManager", (), {})
    utils_pkg.reuse_mesh = lambda *a, **k: None
    utils_pkg.run_aoa_sweep = lambda *a, **k: None
    multishot_mod.load_multishot_project = lambda path: None

    monkeypatch.setitem(sys.modules, "glacium", glacium_pkg)
    monkeypatch.setitem(sys.modules, "glacium.api", types.ModuleType("glacium.api"))
    sys.modules["glacium.api"].Project = Project
    monkeypatch.setitem(sys.modules, "glacium.utils", utils_pkg)
    monkeypatch.setitem(sys.modules, "glacium.utils.logging", logging_pkg)
    monkeypatch.setitem(sys.modules, "glacium.managers", managers_pkg)
    monkeypatch.setitem(sys.modules, "glacium.managers.project_manager", pm_pkg)
    monkeypatch.setitem(sys.modules, "glacium.managers.config_manager", cfg_pkg)
    monkeypatch.setitem(sys.modules, "multishot_loader", multishot_mod)

    # load script
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{filename}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class DummyProject:
    def __init__(self, root: Path):
        self.root = root
        self.uid = "uid"
        self._params = {}
        self._jobs = []
        self.runs_root = None

    def clone(self):
        return DummyProject(self.root)

    def name(self, _name: str):
        return self

    def set(self, key, value):
        pass

    def get(self, key):
        if key in self._params:
            return self._params[key]
        raise KeyError(key)


def test_clean_sweep_precomputed(tmp_path, monkeypatch):
    clean = _load_script(monkeypatch, "08_clean_sweep_creation", "clean_sweep")

    baseline = DummyProject(tmp_path)

    class PM:
        def __init__(self, _root):
            pass

        def list_uids(self):
            return ["uid"]

    monkeypatch.setattr(clean, "ProjectManager", PM)
    monkeypatch.setattr(clean.Project, "load", classmethod(lambda cls, root, uid: baseline))

    ms_project = types.SimpleNamespace(get_mesh=lambda: tmp_path / "mesh.cgns")
    monkeypatch.setattr(clean, "load_multishot_project", lambda path: ms_project)

    run_mock = Mock()
    monkeypatch.setattr(clean, "run_aoa_sweep", run_mock)

    clean.main(base_dir=tmp_path)

    assert run_mock.call_count == 1
    kwargs = run_mock.call_args.kwargs
    assert kwargs["precomputed"] == {0.0: baseline}
    assert kwargs["skip_aoas"] == {0.0}


def test_iced_sweep_precomputed(tmp_path, monkeypatch):
    iced = _load_script(monkeypatch, "10_iced_sweep_creation", "iced_sweep")

    baseline = DummyProject(tmp_path)

    class PM:
        def __init__(self, _root):
            pass

        def list_uids(self):
            return ["uid"]

    monkeypatch.setattr(iced, "ProjectManager", PM)
    monkeypatch.setattr(iced.Project, "load", classmethod(lambda cls, root, uid: baseline))

    ms_root = tmp_path / "ms"
    run_multishot = ms_root / "run_MULTISHOT"
    run_multishot.mkdir(parents=True)
    (run_multishot / "grid.ice.000001").write_text("")
    (run_multishot / "roughness.dat.ice.000001").write_text("")
    ms_project = types.SimpleNamespace(root=ms_root)
    monkeypatch.setattr(iced, "load_multishot_project", lambda path: ms_project)

    run_mock = Mock()
    monkeypatch.setattr(iced, "run_aoa_sweep", run_mock)

    iced.main(base_dir=tmp_path)

    assert run_mock.call_count == 1
    kwargs = run_mock.call_args.kwargs
    assert kwargs["precomputed"] == {0.0: baseline}
    assert kwargs["skip_aoas"] == {0.0}
    assert kwargs["stall_detection_start"] == 2.0
