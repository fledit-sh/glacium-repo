import yaml
from pathlib import Path
from click.testing import CliRunner

from glacium.cli import cli


def test_cli_sweep(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["sweep", "8", "-n", "2", "-f", "2"] , env=env)
        assert result.exit_code == 0
        uids = result.output.strip().splitlines()
        assert len(uids) == 2
        val = 8
        for uid in uids:
            cfg = Path("runs") / uid / "_cfg" / "global_config.yaml"
            data = yaml.safe_load(cfg.read_text())
            assert data["PWS_REFINEMENT"] == val
            val *= 2
