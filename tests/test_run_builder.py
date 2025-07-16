import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.api import Run
from glacium.managers.template_manager import TemplateManager


def test_run_builder_creates_files(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = (
        Run(tmp_path)
        .name("demo")
        .set("MULTISHOT_COUNT", 3)
        .add_job("POINTWISE_MESH2")
    )

    project = run.create()

    cfg_file = tmp_path / project.uid / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    assert cfg["MULTISHOT_COUNT"] == 3

    jobs_file = tmp_path / project.uid / "_cfg" / "jobs.yaml"
    jobs = yaml.safe_load(jobs_file.read_text())
    assert "POINTWISE_MESH2" in jobs
    assert "XFOIL_REFINE" in jobs


def test_run_clone_independent(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    base = Run(tmp_path).name("base").set("MULTISHOT_COUNT", 1).add_job("POINTWISE_MESH2")
    clone = base.clone().name("clone").set("MULTISHOT_COUNT", 2).add_job("CONVERGENCE_STATS")

    base_proj = base.create()
    clone_proj = clone.create()

    base_cfg = yaml.safe_load((tmp_path / base_proj.uid / "_cfg" / "global_config.yaml").read_text())
    clone_cfg = yaml.safe_load((tmp_path / clone_proj.uid / "_cfg" / "global_config.yaml").read_text())

    assert base_cfg["MULTISHOT_COUNT"] == 1
    assert clone_cfg["MULTISHOT_COUNT"] == 2
    assert "CONVERGENCE_STATS" not in yaml.safe_load((tmp_path / base_proj.uid / "_cfg" / "jobs.yaml").read_text())
    clone_jobs = yaml.safe_load((tmp_path / clone_proj.uid / "_cfg" / "jobs.yaml").read_text())
    assert "POINTWISE_MESH2" in clone_jobs
    assert "CONVERGENCE_STATS" in clone_jobs
