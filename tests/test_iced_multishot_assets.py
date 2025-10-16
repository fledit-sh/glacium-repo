"""Tests for iced multishot asset selection helpers."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_script_module(filename: str, module_name: str):
    script = Path(__file__).resolve().parents[1] / "scripts" / filename
    repo_root = str(script.parents[1])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    if "pandas" not in sys.modules:
        sys.modules["pandas"] = types.ModuleType("pandas")
    if "scienceplots" not in sys.modules:
        sys.modules["scienceplots"] = types.ModuleType("scienceplots")
    if "glacium" not in sys.modules:
        glacium_mod = types.ModuleType("glacium")
        api_mod = types.ModuleType("glacium.api")

        class _StubProject:
            @classmethod
            def load(cls, *_args, **_kwargs):  # pragma: no cover - replaced in tests
                raise RuntimeError("Project.load should be patched in tests")

        api_mod.Project = _StubProject  # type: ignore[attr-defined]

        managers_mod = types.ModuleType("glacium.managers")
        pm_mod = types.ModuleType("glacium.managers.project_manager")

        class _StubProjectManager:  # pragma: no cover - replaced in tests
            def __init__(self, *_args, **_kwargs):
                raise RuntimeError("ProjectManager should be patched in tests")

        pm_mod.ProjectManager = _StubProjectManager  # type: ignore[attr-defined]
        managers_mod.project_manager = pm_mod  # type: ignore[attr-defined]

        utils_mod = types.ModuleType("glacium.utils")

        def _stub_reuse_mesh(*_args, **_kwargs):  # pragma: no cover - replaced in tests
            raise RuntimeError("reuse_mesh should be patched in tests")

        def _stub_run_aoa_sweep(*_args, **_kwargs):  # pragma: no cover - replaced in tests
            raise RuntimeError("run_aoa_sweep should be patched in tests")

        utils_mod.reuse_mesh = _stub_reuse_mesh  # type: ignore[attr-defined]
        utils_mod.run_aoa_sweep = _stub_run_aoa_sweep  # type: ignore[attr-defined]

        logging_mod = types.ModuleType("glacium.utils.logging")

        class _StubLogger:
            def error(self, *_args, **_kwargs):  # pragma: no cover - no-op
                pass

        logging_mod.log = _StubLogger()  # type: ignore[attr-defined]
        utils_mod.logging = logging_mod  # type: ignore[attr-defined]

        glacium_mod.api = api_mod  # type: ignore[attr-defined]
        glacium_mod.utils = utils_mod  # type: ignore[attr-defined]
        glacium_mod.managers = managers_mod  # type: ignore[attr-defined]

        sys.modules["glacium"] = glacium_mod
        sys.modules["glacium.api"] = api_mod
        sys.modules["glacium.managers"] = managers_mod
        sys.modules["glacium.managers.project_manager"] = pm_mod
        sys.modules["glacium.utils"] = utils_mod
        sys.modules["glacium.utils.logging"] = logging_mod
    if "multishot_loader" not in sys.modules:
        loader_stub = types.ModuleType("multishot_loader")

        def _missing_loader(*_args, **_kwargs):  # pragma: no cover - patched in tests
            raise RuntimeError("multishot_loader.load_multishot_project not patched")

        loader_stub.load_multishot_project = _missing_loader  # type: ignore[attr-defined]
        sys.modules["multishot_loader"] = loader_stub
    spec = importlib.util.spec_from_file_location(module_name, script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


@pytest.fixture()
def iced_sweep_module():
    return _load_script_module("10_iced_sweep_creation.py", "iced_sweep_test_module")


@pytest.fixture()
def aoa0_module():
    return _load_script_module("07_aoa0_projects.py", "aoa0_test_module")


def test_get_last_iced_grid_uses_case_multishot_index(tmp_path, iced_sweep_module):
    run_dir = tmp_path / "run_MULTISHOT"
    run_dir.mkdir()
    expected = run_dir / "grid.ice.000002"
    expected.touch()

    def _get(key: str):
        if key == "CASE_MULTISHOT":
            return ["shot_a", "shot_b"]
        return None

    project = SimpleNamespace(root=tmp_path, get=_get)
    path, index = iced_sweep_module.get_last_iced_grid(project)
    assert path == expected
    assert index == "000002"

    expected.unlink()
    with pytest.raises(FileNotFoundError):
        iced_sweep_module.get_last_iced_grid(project)


class _FakeProjectBuilder:
    def __init__(self, path: Path) -> None:
        self.root = Path(path)
        self._name = "project"
        self.params: dict[str, object] = {}
        self.jobs: list[str] = []

    def name(self, value: str):
        self._name = value
        return self

    def set(self, key: str, value):
        self.params[key] = value
        return self

    def clone(self):
        other = _FakeProjectBuilder(self.root)
        other._name = self._name
        other.params = dict(self.params)
        other.jobs = list(self.jobs)
        return other

    def add_job(self, job: str):
        self.jobs.append(job)
        return self

    def create(self):
        return _FakeCreatedProject(self.root / self._name)

    @classmethod
    def load(cls, base_path: Path, uid):
        return _FakeCreatedProject(Path(base_path) / str(uid))


class _FakeCreatedProject:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def run(self) -> None:  # pragma: no cover - no behaviour to verify
        pass


class _FakeProjectManager:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def list_uids(self):
        return ["baseline"]


class _DummyMultishotProject:
    def __init__(self, root: Path, shots):
        self.root = Path(root)
        self._shots = shots

    def get(self, key: str):
        if key == "CASE_MULTISHOT":
            return list(self._shots)
        if key == "CASE_CHARACTERISTIC_LENGTH":
            return 1.0
        return None

    def get_mesh(self):
        return self.root / "mesh.cgns"


def _install_common_stubs(module, monkeypatch, multishot_project):
    monkeypatch.setattr(module, "load_multishot_project", lambda _path: multishot_project)
    if hasattr(module, "Project"):
        monkeypatch.setattr(module, "Project", _FakeProjectBuilder)
    if hasattr(module, "ProjectManager"):
        monkeypatch.setattr(module, "ProjectManager", _FakeProjectManager)

    created: list[tuple[Path, Path | None]] = []

    def _fake_reuse(proj, mesh_path, _job, roughness=None):
        created.append((Path(mesh_path), Path(roughness) if roughness else None))

    if hasattr(module, "reuse_mesh"):
        monkeypatch.setattr(module, "reuse_mesh", _fake_reuse)

    if hasattr(module, "run_aoa_sweep"):
        def _fake_run_aoa_sweep(base, *args, **kwargs):
            mesh_hook = kwargs.get("mesh_hook")
            if mesh_hook is not None:
                mesh_hook(_FakeCreatedProject(base.root / "aoa"))
            return [], _FakeCreatedProject(base.root / "aoa")

        monkeypatch.setattr(module, "run_aoa_sweep", _fake_run_aoa_sweep)

    return created


def test_iced_sweep_main_raises_when_roughness_missing(
    tmp_path, iced_sweep_module, monkeypatch
):
    ms_root = tmp_path / "05_multishot"
    run_dir = ms_root / "run_MULTISHOT"
    run_dir.mkdir(parents=True)
    grid = run_dir / "grid.ice.000002"
    grid.touch()

    multishot = _DummyMultishotProject(ms_root, [1, 2])

    reuse_calls = _install_common_stubs(iced_sweep_module, monkeypatch, multishot)

    with pytest.raises(FileNotFoundError) as excinfo:
        iced_sweep_module.main(base_dir=tmp_path)

    assert "roughness" in str(excinfo.value)
    assert "000002" in str(excinfo.value)
    assert not reuse_calls


def test_aoa0_main_raises_when_roughness_missing(
    tmp_path, aoa0_module, iced_sweep_module, monkeypatch
):
    ms_root = tmp_path / "05_multishot"
    run_dir = ms_root / "run_MULTISHOT"
    run_dir.mkdir(parents=True)
    grid = run_dir / "grid.ice.000002"
    grid.touch()

    mesh = ms_root / "mesh.cgns"
    mesh.touch()

    multishot = _DummyMultishotProject(ms_root, ["s1", "s2"])

    # Ensure aoa0 uses the preloaded iced sweep module helpers
    monkeypatch.setattr(aoa0_module, "_load_iced_sweep_module", lambda: iced_sweep_module)
    reuse_calls = _install_common_stubs(aoa0_module, monkeypatch, multishot)

    with pytest.raises(FileNotFoundError) as excinfo:
        aoa0_module.main(base_dir=tmp_path)

    assert "roughness" in str(excinfo.value)
    assert "000002" in str(excinfo.value)
    assert all(roughness is None for _, roughness in reuse_calls)
