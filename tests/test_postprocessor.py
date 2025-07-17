import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.post import PostProcessor, write_manifest
from glacium.post.artifact import ArtifactSet, Artifact


def test_postprocessor_indexing(tmp_path):
    run1 = tmp_path / "run1"
    run2 = tmp_path / "run2"
    run1.mkdir()
    run2.mkdir()

    (run1 / "a.dat").write_text("1")
    (run2 / "b.dat").write_text("2")
    (run2 / "c.dat").write_text("3")

    class DummyImporter:
        def detect(self, root: Path) -> bool:
            return any(root.glob("*.dat"))

        def parse(self, root: Path) -> ArtifactSet:
            aset = ArtifactSet(root.name)
            for p in root.glob("*.dat"):
                aset.add(Artifact(p, p.stem))
            return aset

    pp = PostProcessor(tmp_path, importers=[DummyImporter], recursive=True)

    assert len(pp.index) == 2
    aset = pp.get("run1")
    assert len(aset.artifacts) == 1
    art = aset.get_first("a")
    assert art is not None
    assert art.path.read_text() == "1"

    mapped = set(pp.map("*.dat"))
    assert mapped == {run1 / "a.dat", run2 / "b.dat", run2 / "c.dat"}


def test_postprocessor_manifest(tmp_path, monkeypatch):
    run = tmp_path / "run1"
    run.mkdir()
    (run / "a.dat").write_text("1")

    class DummyImporter:
        def detect(self, root: Path) -> bool:
            return True

        def parse(self, root: Path) -> ArtifactSet:
            aset = ArtifactSet(root.name)
            for p in root.glob("*.dat"):
                aset.add(Artifact(p, p.stem))
            return aset

    pp = PostProcessor(tmp_path, importers=[DummyImporter], recursive=True)
    write_manifest(pp.index, tmp_path / "manifest.json")

    def fail_scan(self):
        raise AssertionError("_scan called")

    monkeypatch.setattr(PostProcessor, "_scan", fail_scan)

    pp2 = PostProcessor(tmp_path, importers=[DummyImporter], recursive=True)
    assert len(pp2.index) == 1
    assert pp2.get("run1").get_first("a") is not None
