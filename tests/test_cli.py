import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from click.testing import CliRunner

from glacium.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--log-level" in result.output


import pytest


@pytest.mark.parametrize(
    "command", ["new", "run", "list", "projects", "select", "job", "sync", "remove"]
)
def test_cli_subcommand_help(command):
    runner = CliRunner()
    result = runner.invoke(cli, [command, "--help"])
    assert result.exit_code == 0


def test_job_global_list():
    runner = CliRunner()
    result = runner.invoke(cli, ["job", "--list"])
    assert result.exit_code == 0
    assert "1)" in result.output
    assert "XFOIL_REFINE" in result.output


def test_cli_logging_options(tmp_path):
    runner = CliRunner()
    log_file = tmp_path / "test.log"
    result = runner.invoke(
        cli, ["--log-level", "DEBUG", "--log-file", str(log_file), "list", "--help"]
    )
    assert result.exit_code == 0
    assert log_file.exists()


def test_cli_log_env():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"], env={"GLACIUM_LOG_LEVEL": "DEBUG"})
    assert result.exit_code == 0
