import math
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
import yaml


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


def _create_project(tmp_path, monkeypatch, *, root: Path | None = None, roughness: str = "roughness_000123.dat"):
    dummy = tmp_path / "defaults.yaml"
    monkeypatch.setattr(default_paths, "global_default_config", lambda: dummy)

    project_root = Path(root) if root is not None else tmp_path
    project_root.mkdir(parents=True, exist_ok=True)

    cfg = GlobalConfig(project_uid="uid", base_dir=project_root)
    cfg["FSP_CHARAC_LENGTH"] = 10.0
    cfg["FSP_FILE_VARIABLE_ROUGHNESS"] = roughness

    paths = PathBuilder(project_root).build()
    return Project("uid", project_root, cfg, paths, [])


TEC_TEMPLATE = """TITLE = \"test\"
VARIABLES = \"X\" \"Y\"
ZONE T=\"surf\", N=3, E=0, DATAPACKING=POINT
0 0
1.5 0
3.0 0
"""


def _setup_multishot_environment(tmp_path: Path) -> Path:
    base = tmp_path / "runs"
    solver_root = base / "05_solver" / "active"
    multishot_root = base / "05_multishot"

    solver_root.mkdir(parents=True, exist_ok=True)
    multishot_root.mkdir(parents=True, exist_ok=True)

    proj_root = multishot_root / "proj_b"
    (proj_root / "_cfg").mkdir(parents=True)
    for name in ["_tmpl", "_data", "mesh", "runs"]:
        (proj_root / name).mkdir(exist_ok=True)

    cfg = {
        "PROJECT_UID": "proj_b",
        "BASE_DIR": str(proj_root),
        "RECIPE": "CUSTOM",
        "CASE_MULTISHOT": ["000001", "000002"],
    }
    (proj_root / "_cfg" / "global_config.yaml").write_text(
        yaml.safe_dump(cfg, sort_keys=False)
    )

    shot_dir = proj_root / "analysis" / "MULTISHOT" / "000002"
    shot_dir.mkdir(parents=True)
    (shot_dir / "merged.dat").write_text(TEC_TEMPLATE)

    return solver_root


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


def test_fensap_run_job_iced_context_model_project(monkeypatch, tmp_path):
    solver_root = _setup_multishot_environment(tmp_path)
    roughness = "roughness.dat.ice.000002.disp"
    project = _create_project(
        tmp_path,
        monkeypatch,
        root=solver_root,
        roughness=roughness,
    )

    job = FensapRunJob(project)
    ctx = job._context()

    assert math.isclose(ctx["FSP_CHARAC_LENGTH_ICED"], 3.0)
    expected_area = 3.0 * 0.1 * project.config["FSP_CHARAC_LENGTH"]
    assert math.isclose(ctx["FSP_REF_AREA_ICED"], expected_area)
