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
