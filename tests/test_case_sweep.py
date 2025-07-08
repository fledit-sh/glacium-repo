import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml


from click.testing import CliRunner
from glacium.cli.case_sweep import cli_case_sweep
from glacium.managers.project_manager import ProjectManager

def test_case_sweep_creates_projects(tmp_path, monkeypatch):
    counter = 0

    def fake_uid(name: str) -> str:
        nonlocal counter
        counter += 1
        return f"uid-{counter}"

    monkeypatch.setattr(ProjectManager, "_uid", staticmethod(fake_uid))

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        cli_case_sweep.callback(
            (
                "CASE_AOA=0,4",
                "CASE_VELOCITY=50,100",
            ),
            recipe="multishot",
            output=Path("runs"),
        )

        uids = [p.name for p in Path("runs").iterdir() if p.is_dir()]
        assert len(uids) == 4

        combos = set()
        for uid in uids:
            case_file = Path("runs") / uid / "case.yaml"
            cfg_file = Path("runs") / uid / "_cfg" / "global_config.yaml"
            assert case_file.exists()
            assert cfg_file.exists()
            case = yaml.safe_load(case_file.read_text())
            cfg = yaml.safe_load(cfg_file.read_text())
            combos.add((case["CASE_AOA"], case["CASE_VELOCITY"]))
            assert cfg["CASE_AOA"] == case["CASE_AOA"]
            assert cfg["CASE_VELOCITY"] == case["CASE_VELOCITY"]

        assert combos == {(0, 50), (0, 100), (4, 50), (4, 100)}


