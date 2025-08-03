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
