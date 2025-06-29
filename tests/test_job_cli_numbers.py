import yaml
from pathlib import Path
from click.testing import CliRunner
from glacium.cli import cli
from glacium.managers.PathManager import _SharedState


def _setup(tmp_path):
    env = {"HOME": str(tmp_path)}
    _SharedState._SharedState__shared_state.clear()
    runner = CliRunner()
    res = runner.invoke(cli, ["new", "proj", "-y"], env=env)
    uid = res.output.strip().splitlines()[-1]
    runner.invoke(cli, ["select", uid], env=env)
    return runner, uid, env


def test_list_numbering(tmp_path):
    runner, uid, env = _setup(tmp_path)
    res = runner.invoke(cli, ["list"], env=env)
    assert res.exit_code == 0
    assert "1   XFOIL_REFINE" in res.output


def test_job_select_and_remove_by_index(tmp_path):
    runner, uid, env = _setup(tmp_path)
    res = runner.invoke(cli, ["job", "select", "1"], env=env)
    assert res.exit_code == 0
    first = res.output.strip()
    from glacium.utils.current_job import load as load_job
    assert load_job() == first

    res = runner.invoke(cli, ["job", "remove", "1"], env=env)
    assert res.exit_code == 0
    jobs_yaml = Path("runs") / uid / "_cfg" / "jobs.yaml"
    data = yaml.safe_load(jobs_yaml.read_text())
    assert first not in data


def test_job_add_by_index(tmp_path):
    runner, uid, env = _setup(tmp_path)
    res = runner.invoke(cli, ["job", "add", "1"], env=env)
    assert res.exit_code == 0
    jobs_yaml = Path("runs") / uid / "_cfg" / "jobs.yaml"
    data = yaml.safe_load(jobs_yaml.read_text())
    assert "HelloJob" in data
