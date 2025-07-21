import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.post import (
    FensapSingleImporter,
    FensapMultiImporter,
    PostProcessor,
)


def test_importer_registration():
    assert FensapSingleImporter in PostProcessor._registry
    assert FensapMultiImporter in PostProcessor._registry


def test_fensap_single_importer(tmp_path):
    run_dir = tmp_path / "run_FENSAP"
    run_dir.mkdir()
    dat = run_dir / "Cl.dat"
    dat.write_text("data")

    imp = FensapSingleImporter()
    assert imp.detect(run_dir)
    aset = imp.parse(run_dir)
    assert aset.run_id == "run_FENSAP"
    art = aset.get_first("Cl")
    assert art is not None
    assert art.path == dat


def test_fensap_multi_importer(tmp_path):
    ms_dir = tmp_path / "run_MULTISHOT"
    sub = ms_dir / "sub"
    sub.mkdir(parents=True)
    (ms_dir / "soln.fensap.000001.dat").write_text("a")
    (sub / "droplet.drop.000002.dat").write_text("b")

    imp = FensapMultiImporter()
    assert imp.detect(ms_dir)
    pipe = imp.parse(ms_dir)
    shots = sorted(r.parameters["SHOT_ID"] for r in pipe)
    assert shots == ["000001", "000002"]
    for run in pipe:
        assert "imported" in run.tags
        assert run.airfoil == "imported"
