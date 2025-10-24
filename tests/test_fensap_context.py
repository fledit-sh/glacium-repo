import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Avoid executing glacium/__init__.py by pre-creating a minimal package
pkg = types.ModuleType("glacium")
pkg.__path__ = [str(ROOT / "glacium")]
sys.modules.setdefault("glacium", pkg)

from glacium.engines.fensap import FensapScriptJob
from glacium.jobs.fensap_jobs import FensapRunJob
from glacium.models.config import GlobalConfig
from glacium.models.project import Project
from glacium.managers.path_manager import PathBuilder
from glacium.utils import default_paths


def test_fensap_context_multishot_sum(monkeypatch, tmp_path):
    dummy = tmp_path / "defaults.yaml"  # does not exist
    monkeypatch.setattr(default_paths, "global_default_config", lambda: dummy)

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["CASE_MULTISHOT"] = [1, 2, 3]

    paths = PathBuilder(tmp_path).build()
    project = Project("uid", tmp_path, cfg, paths, [])

    job = FensapScriptJob(project)
    ctx = job._context()
    assert ctx["ICE_GUI_TOTAL_TIME"] == sum(cfg["CASE_MULTISHOT"])


def _create_project(tmp_path, monkeypatch):
    dummy = tmp_path / "defaults.yaml"
    monkeypatch.setattr(default_paths, "global_default_config", lambda: dummy)

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FSP_CHARAC_LENGTH"] = 10.0
    cfg["FSP_FILE_VARIABLE_ROUGHNESS"] = "roughness_000123.dat"

    paths = PathBuilder(tmp_path).build()
    return Project("uid", tmp_path, cfg, paths, [])


def test_fensap_run_job_iced_context(monkeypatch, tmp_path):
    project = _create_project(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "glacium.jobs.fensap_jobs.compute_iced_char_length", lambda project: 5.0
    )

    job = FensapRunJob(project)
    ctx = job._context()

    assert ctx["FSP_CHARAC_LENGTH_ICED"] == 5.0
    assert ctx["FSP_REF_AREA_ICED"] == 5.0 * 0.1 * 10.0


def test_fensap_run_job_iced_context_fallback(monkeypatch, tmp_path):
    project = _create_project(tmp_path, monkeypatch)

    def _raise(_project):
        raise RuntimeError("boom")

    monkeypatch.setattr("glacium.jobs.fensap_jobs.compute_iced_char_length", _raise)

    job = FensapRunJob(project)
    ctx = job._context()

    assert ctx["FSP_CHARAC_LENGTH_ICED"] == project.config["FSP_CHARAC_LENGTH"]
    assert ctx["FSP_REF_AREA_ICED"] == 10.0 * 0.1 * 10.0
