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


@pytest.mark.parametrize('command', ['new', 'run', 'list', 'projects', 'select', 'job', 'sync', 'remove'])
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
