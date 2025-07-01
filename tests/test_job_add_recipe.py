import yaml
from click.testing import CliRunner
from glacium.constants import RUNS_DIR
from glacium.cli import cli
from glacium.managers.PathManager import _SharedState


def test_job_add_recipe(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}
    _SharedState._SharedState__shared_state.clear()

    result = runner.invoke(cli, ["new", "proj", "-y"], env=env)
    assert result.exit_code == 0
    uid = result.output.strip().splitlines()[-1]

    result = runner.invoke(cli, ["select", uid], env=env)
    assert result.exit_code == 0

    result = runner.invoke(cli, ["job", "add", "--recipe", "pointwise"], env=env)
    assert result.exit_code == 0
    jobs_yaml = RUNS_DIR / uid / "_cfg" / "jobs.yaml"
    data = yaml.safe_load(jobs_yaml.read_text())
    assert "POINTWISE_MESH2" in data
    assert "FLUENT2FENSAP" in data
