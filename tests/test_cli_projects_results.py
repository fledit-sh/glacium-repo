import yaml
from pathlib import Path
from click.testing import CliRunner

from glacium.cli import cli


def test_cli_projects_results(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path), "COLUMNS": "400"}

    with runner.isolated_filesystem(temp_dir=tmp_path):
        res = runner.invoke(cli, ["new", "demo", "-y"], env=env)
        assert res.exit_code == 0
        uid = res.output.strip().splitlines()[-1]

        proj_dir = Path("runs") / uid / "run_MULTISHOT"
        proj_dir.mkdir(parents=True, exist_ok=True)

        # fake solver output
        (proj_dir / ".solvercmd.out").write_text("total simulation = 00:05:00")

        content = "\n".join([
            "# 1 lift coefficient",
            "# 1 drag coefficient",
            "1 2",
            "3 4",
        ])
        (proj_dir / "converg.fensap.000001").write_text(content)

        result = runner.invoke(cli, ["projects", "--results"], env=env)
        assert result.exit_code == 0

        import re
        ansi = re.compile(r"\x1b\[[0-9;]*[mK]")
        clean = ansi.sub("", result.output)

        assert "00:05:00" in clean
        assert "2.000" in clean
        assert "0.000" in clean
        assert "3.000" in clean
