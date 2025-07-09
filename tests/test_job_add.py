import sys
import yaml
from pathlib import Path
from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.cli import cli
from glacium.managers.template_manager import TemplateManager


def test_job_add_with_deps(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    result = runner.invoke(cli, ["new", "proj", "-y"], env=env)
    assert result.exit_code == 0
    uid = result.output.strip().splitlines()[-1]

    result = runner.invoke(cli, ["select", uid], env=env)
    assert result.exit_code == 0

    result = runner.invoke(cli, ["job", "add", "POINTWISE_MESH2"], env=env)
    assert result.exit_code == 0
    assert "POINTWISE_MESH2 hinzugefügt." in result.output

    jobs_yaml = Path("runs") / uid / "_cfg" / "jobs.yaml"
    data = yaml.safe_load(jobs_yaml.read_text())
    assert "POINTWISE_GCI" in data
    assert "POINTWISE_MESH2" in data

    cfg_file = Path("runs") / uid / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    assert cfg["RECIPE"] == "CUSTOM"


def test_job_add_renders_script(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    result = runner.invoke(cli, ["new", "proj", "-y"], env=env)
    assert result.exit_code == 0
    uid = result.output.strip().splitlines()[-1]
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")

    result = runner.invoke(cli, ["select", uid], env=env)
    assert result.exit_code == 0

    result = runner.invoke(cli, ["job", "add", "POINTWISE_MESH2"], env=env)
    assert result.exit_code == 0

    script = Path("runs") / uid / "pointwise" / "POINTWISE.mesh2.glf"
    assert script.exists()


def test_job_add_multiple_custom(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    res = runner.invoke(cli, ["new", "proj", "-y"], env=env)
    assert res.exit_code == 0
    uid = res.output.strip().splitlines()[-1]

    res = runner.invoke(cli, ["select", uid], env=env)
    assert res.exit_code == 0

    res = runner.invoke(cli, ["job", "add", "POINTWISE_MESH2"], env=env)
    assert res.exit_code == 0

    res = runner.invoke(cli, ["job", "add", "POINTWISE_GCI"], env=env)
    assert res.exit_code == 0

    jobs_yaml = Path("runs") / uid / "_cfg" / "jobs.yaml"
    data = yaml.safe_load(jobs_yaml.read_text())
    assert "POINTWISE_MESH2" in data
    assert "POINTWISE_GCI" in data

    cfg_file = Path("runs") / uid / "_cfg" / "global_config.yaml"
    cfg = yaml.safe_load(cfg_file.read_text())
    assert cfg["RECIPE"] == "CUSTOM"


def test_job_list_available_custom(tmp_path):
    TemplateManager(Path(__file__).resolve().parents[1] / "glacium" / "templates")
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    res = runner.invoke(cli, ["new", "proj", "-y"], env=env)
    assert res.exit_code == 0
    uid = res.output.strip().splitlines()[-1]

    res = runner.invoke(cli, ["select", uid], env=env)
    assert res.exit_code == 0

    res = runner.invoke(cli, ["job", "add", "POINTWISE_MESH2"], env=env)
    assert res.exit_code == 0

    res = runner.invoke(cli, ["job", "list", "--available"], env=env)
    assert res.exit_code == 0
