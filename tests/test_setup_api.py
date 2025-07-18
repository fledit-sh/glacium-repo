import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.setup import update


def test_update_replaces_file(tmp_path):
    root = tmp_path
    (root / "config" / "custom").mkdir(parents=True)
    (root / "config" / "defaults").mkdir(parents=True)

    src = root / "config" / "custom" / "fensap.yaml"
    dest = root / "config" / "defaults" / "global_default.yaml"

    src.write_text("A: 1\n")
    dest.write_text("A: 0\n")

    result = update("global_default.yaml", "fensap.yaml", root=root)
    assert result == dest
    assert dest.read_text() == "A: 1\n"
