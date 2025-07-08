import yaml
from pathlib import Path
from click.testing import CliRunner
from glacium.cli import cli


def test_case_sweep_creates_projects(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli,
            [
                "case-sweep",
                "--param",
                "CASE_AOA=0,4",
                "--param",
                "CASE_VELOCITY=50,100",
            ],
            env=env,
        )
        assert result.exit_code == 0
        lines = [l.strip() for l in result.output.splitlines()]
        uids = [l for l in lines if __import__('re').match(r"\d{8}-\d{6}-[0-9A-F]{4}", l)]
        assert len(uids) == 4
        for uid in uids:
            case_file = Path("runs") / uid / "case.yaml"
            cfg_file = Path("runs") / uid / "_cfg" / "global_config.yaml"
            assert case_file.exists()
            assert cfg_file.exists()
            case = yaml.safe_load(case_file.read_text())
            cfg = yaml.safe_load(cfg_file.read_text())
            assert cfg["CASE_AOA"] == case["CASE_AOA"]
            assert cfg["CASE_VELOCITY"] == case["CASE_VELOCITY"]
