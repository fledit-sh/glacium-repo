import yaml
from pathlib import Path
from click.testing import CliRunner

from glacium.cli import cli
from glacium.managers.path_manager import _SharedState


def test_sweep(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}
    _SharedState._SharedState__shared_state.clear()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["sweep", "8"], env=env)
        assert result.exit_code == 0

        uids = result.output.strip().splitlines()
        assert len(uids) == 8

        value = 8
        for uid in uids:
            proj_root = Path("runs") / uid
            cfg = proj_root / "_cfg" / "global_config.yaml"
            data = yaml.safe_load(cfg.read_text())
            assert data["PWS_REFINEMENT"] == value
            assert "CASE_VELOCITY" in data

            jobs_file = proj_root / "_cfg" / "jobs.yaml"
            jobs = yaml.safe_load(jobs_file.read_text())
            assert len(jobs) == 6
            value *= 2
