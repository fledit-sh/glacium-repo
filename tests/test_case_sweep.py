import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml


from glacium.services import CaseSweepService
from glacium.managers.project_manager import ProjectManager


def test_case_sweep_creates_projects(tmp_path, monkeypatch):
    counter = 0

    def fake_uid(name: str) -> str:
        nonlocal counter
        counter += 1
        return f"uid-{counter}"

    monkeypatch.setattr(ProjectManager, "_uid", staticmethod(fake_uid))

    monkeypatch.chdir(tmp_path)
    Path("runs").mkdir()
    service = CaseSweepService(Path("runs"))
    service.create_projects(
        (
            "CASE_AOA=0,4",
            "CASE_VELOCITY=50,100",
            "PWS_REFINEMENT=1,2",
        ),
        recipe="multishot",
        multishots=10,
    )

    uids = [p.name for p in Path("runs").iterdir() if p.is_dir()]
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
