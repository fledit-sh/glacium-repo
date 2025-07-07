import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml
from click.testing import CliRunner

from glacium.cli import cli
from glacium.managers.project_manager import ProjectManager


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
