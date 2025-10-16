from pathlib import Path

import yaml
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.api import Project
from glacium.managers.template_manager import TemplateManager
from glacium.managers.job_manager import JobManager
from glacium.utils import generate_global_defaults, global_default_config
import pytest


def test_project_api_run(tmp_path, monkeypatch):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Project(tmp_path)
    project = run.create()

    called = {}

    def fake_run(self, jobs=None):
        called["jobs"] = jobs

    monkeypatch.setattr(JobManager, "run", fake_run)

    project.run()
    assert called["jobs"] is None

    project.run("XFOIL_REFINE")
    assert called["jobs"] == ["XFOIL_REFINE"]


def test_run_load(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Project(tmp_path)
    project = run.create()

    loaded = Project.load(tmp_path, project.uid)
    assert loaded.uid == project.uid


def test_project_add_job(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Project(tmp_path)
    project = run.create()

    added = project.add_job("CONVERGENCE_STATS")
    assert "CONVERGENCE_STATS" in added
    assert "MULTISHOT_RUN" in added

    jobs_yaml = tmp_path / project.uid / "_cfg" / "jobs.yaml"
    data = yaml.safe_load(jobs_yaml.read_text())
    assert "CONVERGENCE_STATS" in data
    assert "MULTISHOT_RUN" in data

    cfg_file = tmp_path / project.uid / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    assert cfg["RECIPE"] == "CUSTOM"


def test_load_add_job_and_run(tmp_path, monkeypatch):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Project(tmp_path)
    project = run.create()

    uid = project.uid

    proj = Project.load(tmp_path, uid)
    assert proj.uid == uid

    proj.add_job("POINTWISE_MESH2")

    jobs_yaml = tmp_path / uid / "_cfg" / "jobs.yaml"
    data = yaml.safe_load(jobs_yaml.read_text())
    assert "POINTWISE_MESH2" in data
    assert "POINTWISE_GCI" in data

    called = {}

    def fake_run(self, jobs=None):
        called["jobs"] = jobs

    monkeypatch.setattr(JobManager, "run", fake_run)

    proj.run("POINTWISE_MESH2")
    assert called["jobs"] == ["POINTWISE_MESH2"]


def test_project_set_mesh(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Project(tmp_path)
    project = run.create()

    grid_src = tmp_path / "input.grid"
    grid_src.write_text("griddata")
    rough_src = tmp_path / "roughness.dat.ice.000123"
    rough_src.write_text("roughdata")

    project.set_mesh(grid_src, roughness=rough_src)

    dest = project.get_mesh()
    assert dest.read_text() == "griddata"
    rough_dest = project.paths.solver_dir("run_FENSAP") / rough_src.name
    assert rough_dest.read_text() == "roughdata"

    cfg_file = tmp_path / project.uid / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    assert cfg["FSP_FILES_GRID"] == "../mesh/mesh.grid"
    assert cfg["ICE_GRID_FILE"] == "../mesh/mesh.grid"
    assert cfg["FSP_FILE_VARIABLE_ROUGHNESS"] == rough_src.name
    assert cfg["FENSAP_PAR_TEMPLATE"] == "FENSAP.ICEDSWEEP.par.j2"

    selector_file = tmp_path / project.uid / "_cfg" / "template_selector.yaml"
    selector = yaml.safe_load(selector_file.read_text())
    assert selector["FSP_FILE_VARIABLE_ROUGHNESS"] == rough_src.name


def test_project_set_mesh_missing_roughness(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Project(tmp_path)
    project = run.create()

    grid_src = tmp_path / "input.grid"
    grid_src.write_text("griddata")

    with pytest.raises(FileNotFoundError):
        project.set_mesh(grid_src, roughness=tmp_path / "missing.roughness")


def test_project_set_mesh_updates_template_selector(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Project(tmp_path)
    project = run.create()

    selector_file = tmp_path / project.uid / "_cfg" / "template_selector.yaml"
    selector_file.write_text("FSP_FILE_VARIABLE_ROUGHNESS: placeholder\n")

    grid_src = tmp_path / "input.grid"
    grid_src.write_text("griddata")
    rough_src = tmp_path / "roughness.dat.ice.000111"
    rough_src.write_text("roughdata")

    project.set_mesh(
        grid_src, roughness=rough_src, template="../mesh/roughness.template"
    )

    data = yaml.safe_load(selector_file.read_text())
    assert data["FSP_FILE_VARIABLE_ROUGHNESS"] == "../mesh/roughness.template"

    cfg_file = tmp_path / project.uid / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    assert cfg["FENSAP_PAR_TEMPLATE"] == "FENSAP.ICEDSWEEP.par.j2"


def test_project_set_mesh_without_roughness_resets_template_flag(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Project(tmp_path)
    project = run.create()

    grid_src = tmp_path / "input.grid"
    grid_src.write_text("griddata")
    rough_src = tmp_path / "roughness.dat.ice.000999"
    rough_src.write_text("roughdata")

    project.set_mesh(grid_src, roughness=rough_src)

    # Re-run without a roughness file
    new_grid = tmp_path / "input2.grid"
    new_grid.write_text("griddata2")
    project.set_mesh(new_grid)

    cfg_file = tmp_path / project.uid / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    assert "FENSAP_PAR_TEMPLATE" not in cfg
    assert "FSP_FILE_VARIABLE_ROUGHNESS" not in cfg


def test_project_update_non_case_key(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Project(tmp_path)
    project = run.create()

    project.set("FSP_MAX_TIME_STEPS_PER_CYCLE", 999)

    cfg_file = tmp_path / project.uid / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    assert cfg["FSP_MAX_TIME_STEPS_PER_CYCLE"] == 999


def test_project_update_case_key(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    run = Project(tmp_path)
    project = run.create()

    project.set("CASE_VELOCITY", 123.0)

    case_file = tmp_path / project.uid / "case.yaml"
    case = yaml.safe_load(case_file.read_text())
    assert case["CASE_VELOCITY"] == 123.0

    cfg_file = tmp_path / project.uid / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    expected = generate_global_defaults(case_file, global_default_config())
    assert cfg["CASE_VELOCITY"] == 123.0
    assert cfg["FSP_MACH_NUMBER"] == pytest.approx(expected["FSP_MACH_NUMBER"])


def test_project_update_unknown_key(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    project = Project(tmp_path).create()
    with pytest.raises(KeyError):
        project.set("UNKNOWN_KEY", 1)
