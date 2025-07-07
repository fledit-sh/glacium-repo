import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from click.testing import CliRunner
from glacium.cli import cli
import yaml


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0


import pytest


@pytest.mark.parametrize('command', ['new', 'init', 'run', 'list', 'projects', 'select', 'job', 'sync', 'remove', 'generate', 'sweep'])
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
        assert (Path(td) / "runs" / uid / "case.yaml").exists()


def test_cli_generate(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        case_src = Path(__file__).resolve().parents[1] / "glacium" / "config" / "defaults" / "case.yaml"
        case = Path("case.yaml")
        case.write_text(case_src.read_text())
        out = Path("out.yaml")
        result = runner.invoke(cli, ["generate", str(case), "-o", str(out)])
        assert result.exit_code == 0
        data = yaml.safe_load(out.read_text())
        assert data["CASE_AOA"] == 4
