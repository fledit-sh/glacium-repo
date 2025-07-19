import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.api import Run
from glacium.managers.template_manager import TemplateManager
from glacium.utils import generate_global_defaults, global_default_config
import pytest


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


def test_run_builder_unknown_key(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Run(tmp_path).set("UNKNOWN_PARAM", 123)
    with pytest.raises(KeyError):
        run.create()


def test_run_builder_updates_case_key(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Run(tmp_path).set("CASE_VELOCITY", 123)

    project = run.create()

    case_file = tmp_path / project.uid / "case.yaml"
    case = yaml.safe_load(case_file.read_text())
    assert case["CASE_VELOCITY"] == 123


def test_run_builder_mesh_helpers(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Run(tmp_path)

    project = run.create()

    mesh_src = tmp_path / "input.grid"
    mesh_src.write_text("meshdata")
    run.set_mesh(mesh_src, project)

    dest = run.get_mesh(project)
    assert dest.read_text() == "meshdata"

    cfg = yaml.safe_load((tmp_path / project.uid / "_cfg" / "global_config.yaml").read_text())
    assert cfg["FSP_FILES_GRID"] == "../mesh/mesh.grid"
    assert cfg["ICE_GRID_FILE"] == "../mesh/mesh.grid"


def test_run_builder_regenerates_global_config(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Run(tmp_path).set("CASE_VELOCITY", 150)

    project = run.create()

    cfg_file = tmp_path / project.uid / "_cfg" / "global_config.yaml"
    case_file = tmp_path / project.uid / "case.yaml"

    cfg = yaml.safe_load(cfg_file.read_text())
    expected = generate_global_defaults(case_file, global_default_config())

    assert cfg["FSP_MACH_NUMBER"] == pytest.approx(expected["FSP_MACH_NUMBER"])
    assert cfg["PWS_REFINEMENT"] == expected["PWS_REFINEMENT"]
