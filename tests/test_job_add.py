import yaml
from click.testing import CliRunner
from glacium.constants import RUNS_DIR
from glacium.cli import cli
from glacium.managers.PathManager import _SharedState


def test_job_add_with_deps(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}
    _SharedState._SharedState__shared_state.clear()

    result = runner.invoke(cli, ["new", "proj", "-y"], env=env)
    assert result.exit_code == 0
    uid = result.output.strip().splitlines()[-1]

    result = runner.invoke(cli, ["select", uid], env=env)
    assert result.exit_code == 0

    result = runner.invoke(cli, ["job", "add", "POINTWISE_MESH2"], env=env)
    assert result.exit_code == 0
    assert "POINTWISE_MESH2 hinzugefügt." in result.output

    jobs_yaml = RUNS_DIR / uid / "_cfg" / "jobs.yaml"
    data = yaml.safe_load(jobs_yaml.read_text())
    assert "POINTWISE_GCI" in data
    assert "POINTWISE_MESH2" in data
