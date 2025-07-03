import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from click.testing import CliRunner
from glacium.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0


import pytest


@pytest.mark.parametrize('command', ['new', 'init', 'run', 'list', 'projects', 'select', 'job', 'sync', 'remove'])
def test_cli_subcommand_help(command):
    runner = CliRunner()
    result = runner.invoke(cli, [command, '--help'])
    assert result.exit_code == 0


def test_job_global_list():
    runner = CliRunner()
    result = runner.invoke(cli, ['job', '--list'])
    assert result.exit_code == 0
    assert '1)' in result.output
    assert 'XFOIL_REFINE' in result.output


def test_cli_init_creates_project(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}
    from glacium.managers.path_manager import _SharedState
    _SharedState._SharedState__shared_state.clear()

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(cli, ["init"], env=env)
        assert result.exit_code == 0
        uid = result.output.strip()
        cfg = Path(td) / "runs" / uid / "_cfg" / "global_config.yaml"
        assert cfg.exists()
