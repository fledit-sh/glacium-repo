from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.utils.iced import compute_iced_char_length


class DummyProject:
    def __init__(self, root: Path, roughness: str | None):
        self._root = Path(root)
        self._roughness = roughness

    @property
    def root(self) -> Path:
        return self._root

    def get(self, key: str):
        if key.upper() == "FSP_FILE_VARIABLE_ROUGHNESS":
            if self._roughness is None:
                raise KeyError(key)
            return self._roughness
        raise KeyError(key)


TEC_TEMPLATE = """TITLE = \"test\"\nVARIABLES = \"X\" \"Y\"\nZONE T=\"surf\", N=3, E=0, DATAPACKING=POINT\n0 0\n1.5 0\n3.0 0\n"""


def _create_multishot_project(root: Path, uid: str, shots: list[str]) -> Path:
    proj_root = root / uid
    (proj_root / "_cfg").mkdir(parents=True)
    # required companion directories for PathBuilder / JobManager
    for name in ["_tmpl", "_data", "mesh", "runs"]:
        (proj_root / name).mkdir(exist_ok=True)
    cfg = {
        "PROJECT_UID": uid,
        "BASE_DIR": str(proj_root),
        "RECIPE": "CUSTOM",
        "CASE_MULTISHOT": shots,
    }
    (proj_root / "_cfg" / "global_config.yaml").write_text(
        yaml.safe_dump(cfg, sort_keys=False)
    )
    return proj_root


def _prepare_layout(tmp_path: Path) -> tuple[DummyProject, Path, Path]:
    base = tmp_path / "runs"
    solver_root = base / "05_solver"
    multishot_root = base / "05_multishot"
    multishot_root.mkdir(parents=True)
    (solver_root / "active").mkdir(parents=True)

    _create_multishot_project(multishot_root, "proj_a", ["000001"])
    proj_b = _create_multishot_project(
        multishot_root, "proj_b", ["000001", "000002"]
    )
    shot_dir = proj_b / "analysis" / "MULTISHOT" / "000002"
    shot_dir.mkdir(parents=True)
    (shot_dir / "merged.dat").write_text(TEC_TEMPLATE)

    project = DummyProject(solver_root / "active", "roughness.dat.ice.000002.disp")
    return project, multishot_root, proj_b


def test_compute_iced_char_length(tmp_path: Path):
    project, _multishot_root, _proj_b = _prepare_layout(tmp_path)
    length = compute_iced_char_length(project)
    assert math.isclose(length, 3.0)


def test_compute_iced_char_length_missing_file(tmp_path: Path):
    project, _multishot_root, proj_b = _prepare_layout(tmp_path)
    merged = proj_b / "analysis" / "MULTISHOT" / "000002" / "merged.dat"
    merged.unlink()
    length = compute_iced_char_length(project)
    assert math.isnan(length)


def test_compute_iced_char_length_missing_variable(tmp_path: Path):
    project, _multishot_root, _proj_b = _prepare_layout(tmp_path)
    missing = DummyProject(project.root, None)
    with pytest.raises(ValueError):
        compute_iced_char_length(missing)
