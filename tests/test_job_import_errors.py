import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.utils.JobIndex import JobFactory
from click.testing import CliRunner
from glacium.cli import cli
import yaml


def test_missing_dependency_runtime_error(tmp_path, monkeypatch):
    pkg = tmp_path / "fake_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "bad_job.py").write_text(
        "import nonexistent_dependency\nfrom glacium.models.job import Job\nclass BadJob(Job):\n    name = 'BAD_JOB'\n"
    )

    monkeypatch.syspath_prepend(tmp_path)
    monkeypatch.setattr(JobFactory, "_PACKAGES", ["fake_pkg"])
    monkeypatch.setattr(JobFactory, "_jobs", None)
    monkeypatch.setattr(JobFactory, "_loaded", False)
    monkeypatch.setattr(JobFactory, "_import_errors", None)

    with pytest.raises(RuntimeError) as exc:
        JobFactory.create("BAD_JOB", None)

    msg = str(exc.value)
    assert "fake_pkg.bad_job" in msg
    assert "BAD_JOB" in msg


def test_cli_list_with_missing_job(tmp_path, monkeypatch):
    pkg = tmp_path / "fake_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "bad_job.py").write_text(
        "import nonexistent_dependency\nfrom glacium.models.job import Job\nclass BadJob(Job):\n    name = 'BAD_JOB'\n"
    )

    runner = CliRunner()
    env = {"HOME": str(tmp_path)}
    with runner.isolated_filesystem(temp_dir=tmp_path):
        res = runner.invoke(cli, ["new", "proj", "-r", "hello", "-y", "-o", "runs"], env=env)
        assert res.exit_code == 0
        uid = res.output.strip().splitlines()[-1]

        jobs_yaml = Path("runs") / uid / "_cfg" / "jobs.yaml"
        data = yaml.safe_load(jobs_yaml.read_text())
        data["BAD_JOB"] = "PENDING"
        yaml.dump(data, jobs_yaml.open("w"))

        runner.invoke(cli, ["select", uid], env=env)

        monkeypatch.syspath_prepend(tmp_path)
        monkeypatch.setattr(JobFactory, "_PACKAGES", [
            "glacium.recipes",
            "fake_pkg",
        ])
        monkeypatch.setattr(JobFactory, "_loaded", False)
        monkeypatch.setattr(JobFactory, "_import_errors", None)

        res = runner.invoke(cli, ["list"], env=env)
        assert res.exit_code == 0
        assert "BAD_JOB" in res.output
        assert "missing dependency" in res.output

        cfg_file = Path("runs") / uid / "_cfg" / "global_config.yaml"
        cfg = yaml.safe_load(cfg_file.read_text())
        assert cfg["RECIPE"] == "CUSTOM"
