import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import re
import yaml
from click.testing import CliRunner

from glacium.cli import cli
from glacium.managers.project_manager import ProjectManager


def test_cli_case_sweep(tmp_path, monkeypatch):
    counter = 0

    def fake_uid(name: str) -> str:
        nonlocal counter
        counter += 1
        return f"20000101-000000-000000-{counter:04X}"

    monkeypatch.setattr(ProjectManager, "_uid", staticmethod(fake_uid))

    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli,
            [
                "case-sweep",
                "--shot-time",
                "1",
                "--shot-time",
                "2",
                "--param",
                "CASE_AOA=0,4",
                "--param",
                "CASE_VELOCITY=50,100",
                "--param",
                "PWS_REFINEMENT=1,2",
            ],
            env=env,
        )
        assert result.exit_code == 0
        lines = [l.strip() for l in result.output.splitlines()]
        uids = [
            l
            for l in lines
            if re.match(r"\d{8}-\d{6}-\d{6}-[0-9A-F]{4}", l)
        ]
        assert len(uids) == 8

        combos = set()
        for uid in uids:
            case_file = Path("runs") / uid / "case.yaml"
            cfg_file = Path("runs") / uid / "_cfg" / "global_config.yaml"
            assert case_file.exists()
            assert cfg_file.exists()
            case = yaml.safe_load(case_file.read_text())
            cfg = yaml.safe_load(cfg_file.read_text())
            combos.add((case["CASE_AOA"], case["CASE_VELOCITY"], case["PWS_REFINEMENT"]))
            assert cfg["CASE_AOA"] == case["CASE_AOA"]
            assert cfg["CASE_VELOCITY"] == case["CASE_VELOCITY"]
            assert cfg["PWS_REFINEMENT"] == case["PWS_REFINEMENT"]
            assert case["CASE_MULTISHOT"] == [1, 2]
            assert cfg["CASE_MULTISHOT"] == [1, 2]
            assert len(case["CASE_MULTISHOT"]) == 2
            assert len(cfg["CASE_MULTISHOT"]) == 2

        assert combos == {
            (0, 50, 1),
            (0, 50, 2),
            (0, 100, 1),
            (0, 100, 2),
            (4, 50, 1),
            (4, 50, 2),
            (4, 100, 1),
            (4, 100, 2),
        }

