import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import subprocess

from glacium.post.convert.single import SingleShotConverter
from glacium.post.convert.multishot import MultiShotConverter


def test_single_shot_converter(tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    run = proj / "run_FENSAP"
    mesh = proj / "mesh"
    run.mkdir(parents=True)
    mesh.mkdir()

    (mesh / "mesh.grid").write_text("grid")
    (mesh / "grid.ice").write_text("grid")
    (proj / "mesh.grid").write_text("grid")
    src = run / "soln"
    src.write_text("src")

    created = []

    def fake_run(cmd, check, cwd=None):
        Path(cwd, cmd[4]).write_text("dat")
        created.append((cmd, cwd))

    monkeypatch.setattr(subprocess, "run", fake_run)

    conv = SingleShotConverter(run, exe=Path("dummy"))
    out = conv.convert()
    assert out.exists()
    assert out.read_text() == "dat"
    assert created

    created.clear()
    # second call should not run again without overwrite
    conv.convert()
    assert not created


def test_multishot_converter(tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    ms_dir = proj / "analysis" / "run_MULTISHOT"
    mesh = proj / "mesh"
    ms_dir.mkdir(parents=True)
    mesh.mkdir()
    (mesh / "mesh.grid").write_text("grid")

    shot1 = "000001"
    shot2 = "000002"
    shot3 = "000003"

    for s in (shot1, shot2, shot3):
        (mesh / f"grid.ice.{s}").write_text(f"g{s}")

    (ms_dir / f"soln.fensap.{shot1}").write_text("s1")
    (ms_dir / f"droplet.drop.{shot1}").write_text("d1")
    (ms_dir / f"swimsol.ice.{shot2}").write_text("i2")
    (ms_dir / f"swimsol.ice.{shot3}").write_text("i3")

    def fake_run(cmd, check, cwd=None):
        Path(cwd, cmd[4]).write_text("dat")

    monkeypatch.setattr(subprocess, "run", fake_run)

    conv = MultiShotConverter(ms_dir, exe=Path("dummy"), concurrency=1)
    conv.convert_all()

    # Only files with matching input are converted for the middle shot
    assert not (ms_dir / f"soln.fensap.{shot2}.dat").exists()
    assert not (ms_dir / f"droplet.drop.{shot2}.dat").exists()
    assert (ms_dir / f"swimsol.ice.{shot2}.dat").exists()
