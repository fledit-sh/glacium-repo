import yaml
from pathlib import Path
from click.testing import CliRunner
import pytest

from glacium.cli import cli
from glacium.utils import generate_global_defaults, global_default_config


def test_cli_update(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    with runner.isolated_filesystem(temp_dir=tmp_path):
        res = runner.invoke(cli, ["init"], env=env)
        assert res.exit_code == 0
        uid = res.output.strip()
        runner.invoke(cli, ["select", uid], env=env)

        proj_root = Path("runs") / uid
        case_file = proj_root / "case.yaml"
        case = yaml.safe_load(case_file.read_text())
        case["CASE_VELOCITY"] = 123.0
        case_file.write_text(yaml.dump(case, sort_keys=False))

        result = runner.invoke(cli, ["update"], env=env)
        assert result.exit_code == 0

        cfg_file = proj_root / "_cfg" / "global_config.yaml"
        data = yaml.safe_load(cfg_file.read_text())
        expected = generate_global_defaults(case_file, global_default_config())
        assert data["CASE_VELOCITY"] == 123.0
        assert data["FSP_MACH_NUMBER"] == pytest.approx(expected["FSP_MACH_NUMBER"])
        assert data["PWS_REFINEMENT"] == expected["PWS_REFINEMENT"]
        assert data["RECIPE"] == "prep"
        assert data["PROJECT_NAME"] == "project"


def test_cli_update_preserves_recipe(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    with runner.isolated_filesystem(temp_dir=tmp_path):
        res = runner.invoke(cli, ["init", "-r", "hello"], env=env)
        assert res.exit_code == 0
        uid = res.output.strip()
        runner.invoke(cli, ["select", uid], env=env)

        proj_root = Path("runs") / uid
        case_file = proj_root / "case.yaml"
        case = yaml.safe_load(case_file.read_text()) or {}
        case["CASE_VELOCITY"] = 321.0
        case_file.write_text(yaml.dump(case, sort_keys=False))

        result = runner.invoke(cli, ["update"], env=env)
        assert result.exit_code == 0

        cfg_file = proj_root / "_cfg" / "global_config.yaml"
        data = yaml.safe_load(cfg_file.read_text())
        expected = generate_global_defaults(case_file, global_default_config())
        assert data["CASE_VELOCITY"] == 321.0
        assert data["FSP_MACH_NUMBER"] == pytest.approx(expected["FSP_MACH_NUMBER"])
        assert data["PWS_REFINEMENT"] == expected["PWS_REFINEMENT"]
        assert data["RECIPE"] == "hello"
        assert data["PROJECT_NAME"] == "project"
