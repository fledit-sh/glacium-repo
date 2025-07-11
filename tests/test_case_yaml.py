import yaml
from pathlib import Path

from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder, _SharedState
from glacium.managers.config_manager import ConfigManager
from glacium.managers.template_manager import TemplateManager
from glacium.models.project import Project
from glacium.jobs.pointwise_jobs import PointwiseGCIJob
from glacium.engines.pointwise import PointwiseEngine
from glacium.utils.default_paths import global_default_config


def test_case_yaml_updates_pointwise_template(monkeypatch, tmp_path):
    _SharedState._SharedState__shared_state.clear()

    tmpl_root = tmp_path / "tmpl"
    tmpl_root.mkdir()
    (tmpl_root / "POINTWISE.GCI.glf.j2").write_text("ref {{ PWS_REFINEMENT }}")
    TemplateManager(tmpl_root)

    paths = PathBuilder(tmp_path).build()
    paths.ensure()

    defaults_file = global_default_config()
    defaults = yaml.safe_load(defaults_file.read_text()) if defaults_file.exists() else {}
    cfg = GlobalConfig(**defaults, project_uid="uid", base_dir=tmp_path)
    cfg.dump(paths.global_cfg_file())

    (paths.cfg_dir() / "case.yaml").write_text("PWS_REFINEMENT: 42")

    cfg_mgr = ConfigManager(paths)
    cfg = cfg_mgr.merge_subsets(["case"])

    project = Project("uid", tmp_path, cfg, paths, [])
    job = PointwiseGCIJob(project)

    monkeypatch.setattr(PointwiseEngine, "run_script", lambda self, exe, script, work: None)

    job.execute()

    out = (paths.solver_dir("pointwise") / "POINTWISE.GCI.glf").read_text()
    assert "42" in out
