import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml
from click.testing import CliRunner

from glacium.cli import cli
from glacium.managers.project_manager import ProjectManager
from glacium.managers.job_manager import JobManager


def test_run_all_executes_jobs(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    with runner.isolated_filesystem(temp_dir=tmp_path):
        pm = ProjectManager(Path("runs"))
        airfoil = (
            Path(__file__).resolve().parents[1] / "glacium" / "data" / "AH63K127.dat"
        )

        p1 = pm.create("proj1", "hello", airfoil)
        p2 = pm.create("proj2", "hello", airfoil)

        result = runner.invoke(cli, ["run", "--all"], env=env)
        assert result.exit_code == 0

        jobs1 = yaml.safe_load(
            (Path("runs") / p1.uid / "_cfg" / "jobs.yaml").read_text()
        )
        jobs2 = yaml.safe_load(
            (Path("runs") / p2.uid / "_cfg" / "jobs.yaml").read_text()
        )

        assert jobs1.get("HelloJob") == "DONE"
        assert jobs2.get("HelloJob") == "DONE"


def test_run_all_continues_on_error(tmp_path, monkeypatch):
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    with runner.isolated_filesystem(temp_dir=tmp_path):
        pm = ProjectManager(Path("runs"))
        airfoil = (
            Path(__file__).resolve().parents[1] / "glacium" / "data" / "AH63K127.dat"
        )

        p1 = pm.create("proj1", "hello", airfoil)
        p2 = pm.create("proj2", "hello", airfoil)

        called = {}

        def patched_run(self, jobs=None, include_failed=False):
            if self.project.uid == p1.uid:
                raise RuntimeError("boom")
            if self.project.uid == p2.uid:
                called["ok"] = True

        monkeypatch.setattr(JobManager, "run", patched_run)

        result = runner.invoke(cli, ["run", "--all"], env=env)
        assert result.exit_code == 0
        assert called.get("ok")
