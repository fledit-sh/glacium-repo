import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.api import Project
from glacium.managers.template_manager import TemplateManager


def test_clone_loaded_project(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    base = (
        Project(tmp_path)
        .name("base")
        .set("CASE_VELOCITY", 123)
        .add_job("POINTWISE_MESH2")
    )
    base_proj = base.create()

    loaded = Project.load(tmp_path, base_proj.uid)
    clone_builder = loaded.clone().name("clone")
    clone_proj = clone_builder.create()

    cfg_file = tmp_path / clone_proj.uid / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    assert cfg["CASE_VELOCITY"] == 123

    jobs_file = tmp_path / clone_proj.uid / "_cfg" / "jobs.yaml"
    jobs = yaml.safe_load(jobs_file.read_text())
    assert "POINTWISE_MESH2" in jobs
