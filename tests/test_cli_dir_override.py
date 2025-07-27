import yaml
from pathlib import Path
from click.testing import CliRunner

from glacium.cli import cli
from glacium.managers.project_manager import ProjectManager


def test_cli_projects_custom_dir(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path), "COLUMNS": "200"}
    with runner.isolated_filesystem(temp_dir=tmp_path):
        root = Path("other_runs")
        airfoil = (
            Path(__file__).resolve().parents[1]
            / "glacium"
            / "data"
            / "AH63K127.dat"
        )
        pm = ProjectManager(root)
        proj = pm.create("demo", "hello", airfoil)

        result = runner.invoke(cli, ["--dir", str(root), "projects"], env=env)
        assert result.exit_code == 0
        assert proj.uid in result.output


def test_cli_run_all_custom_dir(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}
    with runner.isolated_filesystem(temp_dir=tmp_path):
        root = Path("overridepath")
        airfoil = (
            Path(__file__).resolve().parents[1]
            / "glacium"
            / "data"
            / "AH63K127.dat"
        )
        pm = ProjectManager(root)
        p1 = pm.create("proj1", "hello", airfoil)
        p2 = pm.create("proj2", "hello", airfoil)

        result = runner.invoke(cli, ["--dir", str(root), "run", "--all"], env=env)
        assert result.exit_code == 0

        jobs1 = yaml.safe_load((root / p1.uid / "_cfg" / "jobs.yaml").read_text())
        jobs2 = yaml.safe_load((root / p2.uid / "_cfg" / "jobs.yaml").read_text())
        assert jobs1.get("HelloJob") == "DONE"
        assert jobs2.get("HelloJob") == "DONE"
