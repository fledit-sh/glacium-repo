import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.managers.project_manager import ProjectManager


def test_uid_uniqueness(tmp_path):
    pm = ProjectManager(tmp_path)
    airfoil = Path(__file__).resolve().parents[1] / "glacium" / "data" / "AH63K127.dat"

    uids = [pm.create("proj", "hello", airfoil).uid for _ in range(5)]
    assert len(set(uids)) == len(uids)
