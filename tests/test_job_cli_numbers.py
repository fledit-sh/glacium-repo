import yaml
from pathlib import Path
from click.testing import CliRunner
from glacium.cli import cli
from glacium.managers.job_manager import JobManager


def _setup(tmp_path):
    env = {"HOME": str(tmp_path)}
    runner = CliRunner()
    res = runner.invoke(cli, ["new", "proj", "-y"], env=env)
    uid = res.output.strip().splitlines()[-1]
    assert (Path("runs") / uid / "case.yaml").exists()
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
    from glacium.utils.JobIndex import list_jobs

    first_job = list_jobs()[0]
    assert first_job in data


def test_job_reset_by_index(tmp_path):
    runner, uid, env = _setup(tmp_path)
    jobs_yaml = Path("runs") / uid / "_cfg" / "jobs.yaml"
    # Mark job as DONE
    data = yaml.safe_load(jobs_yaml.read_text())
    data["XFOIL_REFINE"] = "DONE"
    yaml.dump(data, jobs_yaml.open("w"))

    res = runner.invoke(cli, ["job", "reset", "1"], env=env)
    assert res.exit_code == 0
    data = yaml.safe_load(jobs_yaml.read_text())
    assert data["XFOIL_REFINE"] == "PENDING"


def test_job_run_by_index(tmp_path, monkeypatch):
    runner, uid, env = _setup(tmp_path)

    called = {}

    def fake_run(self, jobs=None):
        called["jobs"] = jobs

    monkeypatch.setattr(JobManager, "run", fake_run)

    res = runner.invoke(cli, ["job", "run", "1"], env=env)
    assert res.exit_code == 0
    assert called["jobs"] == ["XFOIL_REFINE"]


def test_remove_updates_listing(tmp_path):
    runner, uid, env = _setup(tmp_path)
    res = runner.invoke(cli, ["job", "remove", "1"], env=env)
    assert res.exit_code == 0

    res = runner.invoke(cli, ["list"], env=env)
    assert res.exit_code == 0
    assert "XFOIL_REFINE" not in res.output

    jobs_yaml = Path("runs") / uid / "_cfg" / "jobs.yaml"
    data = yaml.safe_load(jobs_yaml.read_text())
    assert "XFOIL_REFINE" not in data

